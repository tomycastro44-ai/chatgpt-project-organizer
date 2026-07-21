from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, selectinload

from app.models import Chat, ImportBatch, ImportIssue, Message, SourceFile
from app.services.import_parsers import ParseIssue, UnsupportedImportFormat, detect_format, parse_import_file
from app.services.import_storage import ImportStorage


@dataclass(frozen=True)
class ImportInput:
    filename: str
    content: bytes
    mime_type: str = "application/octet-stream"


class ImportService:
    def __init__(self, engine: Engine, imports_dir: Path, max_file_bytes: int, max_files: int) -> None:
        self.engine = engine
        self.storage = ImportStorage(imports_dir)
        self.max_file_bytes = max_file_bytes
        self.max_files = max_files

    def import_inputs(self, inputs: list[ImportInput], source_kind: str) -> ImportBatch:
        if not inputs:
            raise ValueError("At least one file is required")
        if len(inputs) > self.max_files:
            raise ValueError(f"A maximum of {self.max_files} files can be imported per batch")

        with Session(self.engine) as session:
            batch = ImportBatch(source_kind=source_kind, total_files=len(inputs))
            session.add(batch)
            session.commit()
            session.refresh(batch)
            batch_id = batch.id

        for item in inputs:
            self._import_one(batch_id, item)

        with Session(self.engine) as session:
            batch = session.get(ImportBatch, batch_id)
            if batch is None:
                raise RuntimeError("Import batch disappeared")
            sources = session.scalars(select(SourceFile).where(SourceFile.batch_id == batch_id)).all()
            batch.accepted_files = sum(1 for source in sources if source.status == "ACCEPTED")
            batch.rejected_files = sum(1 for source in sources if source.status == "REJECTED")
            batch.imported_chats = sum(source.chat_count for source in sources)
            batch.imported_messages = sum(source.message_count for source in sources)
            batch.issue_count = sum(source.error_count for source in sources)
            batch.status = "COMPLETED" if batch.issue_count == 0 else "COMPLETED_WITH_ERRORS"
            batch.completed_at = datetime.now(timezone.utc)
            session.commit()
            return self.get_batch(batch_id)

    def _import_one(self, batch_id: str, item: ImportInput) -> None:
        with Session(self.engine) as session:
            source: SourceFile | None = None
            try:
                stored = self.storage.store_original(batch_id, item.filename, item.content)
                try:
                    file_format = detect_format(item.filename)
                except UnsupportedImportFormat as exc:
                    file_format = "unsupported"
                    source = SourceFile(
                        batch_id=batch_id,
                        original_name=item.filename,
                        stored_name=stored.stored_name,
                        format=file_format,
                        mime_type=item.mime_type,
                        size_bytes=stored.size_bytes,
                        sha256=stored.sha256,
                        status="REJECTED",
                        storage_path=stored.relative_path,
                        error_count=1,
                    )
                    session.add(source)
                    session.flush()
                    session.add(ImportIssue(batch_id=batch_id, source_file_id=source.id, scope="FILE", code="UNSUPPORTED_FORMAT", message=str(exc)))
                    session.commit()
                    return

                source = SourceFile(
                    batch_id=batch_id,
                    original_name=item.filename,
                    stored_name=stored.stored_name,
                    format=file_format,
                    mime_type=item.mime_type,
                    size_bytes=stored.size_bytes,
                    sha256=stored.sha256,
                    status="PROCESSING",
                    storage_path=stored.relative_path,
                )
                session.add(source)
                session.flush()

                if len(item.content) > self.max_file_bytes:
                    issue = ParseIssue("FILE", "FILE_TOO_LARGE", f"File exceeds {self.max_file_bytes} bytes")
                    self._add_issue(session, batch_id, source.id, issue)
                    source.status = "REJECTED"
                    source.error_count = 1
                    session.commit()
                    return

                parsed = parse_import_file(item.filename, item.content)
                for issue in parsed.issues:
                    self._add_issue(session, batch_id, source.id, issue)
                for normalized in parsed.chats:
                    chat = Chat(
                        batch_id=batch_id,
                        source_file_id=source.id,
                        external_id=normalized.external_id,
                        title=normalized.title,
                        created_at=normalized.created_at,
                        updated_at=normalized.updated_at,
                        content_fingerprint=normalized.content_fingerprint,
                        source_index=normalized.source_index,
                    )
                    session.add(chat)
                    session.flush()
                    for position, normalized_message in enumerate(normalized.messages):
                        session.add(
                            Message(
                                chat_id=chat.id,
                                external_id=normalized_message.external_id,
                                position=position,
                                role=normalized_message.role,
                                timestamp=normalized_message.timestamp,
                                content=normalized_message.content,
                            )
                        )
                source.chat_count = len(parsed.chats)
                source.message_count = sum(len(chat.messages) for chat in parsed.chats)
                source.error_count = len(parsed.issues)
                source.status = "ACCEPTED" if parsed.chats else "REJECTED"
                session.commit()
            except Exception as exc:
                session.rollback()
                if source is not None:
                    source_id = source.id
                else:
                    source_id = None
                with Session(self.engine) as recovery:
                    persisted_source_id: str | None = None
                    if source_id is not None:
                        recovered = recovery.get(SourceFile, source_id)
                        if recovered is not None:
                            recovered.status = "REJECTED"
                            recovered.error_count += 1
                            persisted_source_id = recovered.id
                    recovery.add(
                        ImportIssue(
                            batch_id=batch_id,
                            source_file_id=persisted_source_id,
                            scope="FILE",
                            code="IMPORT_FAILURE",
                            message=f"Unexpected import failure: {exc}",
                        )
                    )
                    recovery.commit()

    @staticmethod
    def _add_issue(session: Session, batch_id: str, source_file_id: str, issue: ParseIssue) -> None:
        session.add(
            ImportIssue(
                batch_id=batch_id,
                source_file_id=source_file_id,
                scope=issue.scope,
                code=issue.code,
                severity=issue.severity,
                message=issue.message,
                record_reference=issue.record_reference,
            )
        )

    def list_batches(self, limit: int = 20) -> list[ImportBatch]:
        with Session(self.engine) as session:
            return list(session.scalars(select(ImportBatch).order_by(ImportBatch.created_at.desc()).limit(limit)).all())

    def get_batch(self, batch_id: str) -> ImportBatch:
        with Session(self.engine) as session:
            batch = session.scalar(
                select(ImportBatch)
                .where(ImportBatch.id == batch_id)
                .options(selectinload(ImportBatch.source_files), selectinload(ImportBatch.issues))
            )
            if batch is None:
                raise KeyError(batch_id)
            session.expunge_all()
            return batch

    def list_chats(self, batch_id: str, limit: int = 100, offset: int = 0) -> list[Chat]:
        with Session(self.engine) as session:
            return list(
                session.scalars(
                    select(Chat)
                    .where(Chat.batch_id == batch_id)
                    .order_by(Chat.source_file_id, Chat.source_index)
                    .offset(offset)
                    .limit(limit)
                    .options(selectinload(Chat.messages))
                ).all()
            )

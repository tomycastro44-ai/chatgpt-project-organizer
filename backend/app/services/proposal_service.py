from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.models import (
    AnalysisFinding,
    AppliedOperation,
    AuditEvent,
    Chat,
    Project,
    ProjectMembership,
    ProposalItem,
    ProposalRun,
    SemanticException,
    SemanticRun,
    UndoOperation,
    UserReview,
    WorkspaceState,
)
from app.schemas.proposals import (
    AppliedOperationResponse,
    AuditEventResponse,
    PreviewResponse,
    ProposalItemResponse,
    ProposalRunResponse,
    ProposalRunSummaryResponse,
    UndoOperationResponse,
    UserReviewResponse,
    WorkspaceStateResponse,
)

ALLOWED_CONFIDENCE = {"ALTA", "MEDIA", "BAJA"}
APPLICABLE_STATUSES = {"APPROVED", "CORRECTED", "APPLIED"}


def _loads(raw: str, default: Any) -> Any:
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return default


def _canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _state_hash(value: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


class ProposalService:
    def __init__(self, engine: Engine, settings: Settings) -> None:
        self.engine = engine
        self.settings = settings

    def create_run(self, semantic_run_id: str) -> ProposalRunResponse:
        with Session(self.engine) as session:
            semantic = self._load_semantic(session, semantic_run_id)
            if semantic.status != "COMPLETED":
                raise ValueError("Semantic run must be completed first")
            existing = session.scalar(
                select(ProposalRun).where(ProposalRun.semantic_run_id == semantic_run_id).order_by(ProposalRun.created_at.desc())
            )
            if existing is not None and existing.status not in {"UNDONE", "FAILED"}:
                return self.get_run(existing.id)

            raw_items = self._fixture_items() if semantic.mode == "DEMO" else self._derive_items(semantic)
            run = ProposalRun(
                semantic_run_id=semantic_run_id,
                status="READY",
                safe_count=sum(not item.get("review_required", False) for item in raw_items),
                exception_count=sum(bool(item.get("review_required", False)) for item in raw_items),
                originals_modified=False,
            )
            session.add(run)
            session.flush()
            for index, raw in enumerate(raw_items):
                confidence = raw.get("confidence", "MEDIA")
                if confidence not in ALLOWED_CONFIDENCE:
                    raise ValueError(f"Invalid confidence {confidence}")
                operation = str(raw["operation"])
                target_ids = list(raw.get("target_ids", []))
                item = ProposalItem(
                    proposal_run_id=run.id,
                    stable_key=str(raw.get("id") or f"proposal-{index + 1}"),
                    operation=operation,
                    title=self._title(operation, target_ids),
                    reason=str(raw.get("reason", "Proposal derived from semantic memory.")),
                    confidence=confidence,
                    review_required=bool(raw.get("review_required", False)),
                    status="PENDING_REVIEW" if raw.get("review_required", False) else "READY",
                    target_ids_json=json.dumps(target_ids, ensure_ascii=False),
                    candidate_project_keys_json=json.dumps(raw.get("candidate_project_ids", []), ensure_ascii=False),
                    evidence_ids_json=json.dumps(raw.get("evidence_ids", []), ensure_ascii=False),
                    payload_json=json.dumps(raw, ensure_ascii=False, sort_keys=True),
                    sort_order=index,
                )
                session.add(item)
            session.flush()
            self._audit(session, run.id, "PROPOSAL_RUN_CREATED", {
                "safe_count": run.safe_count,
                "exception_count": run.exception_count,
                "semantic_run_id": semantic_run_id,
            })
            session.commit()
            run_id = run.id
        return self.get_run(run_id)

    def approve_safe(self, run_id: str) -> ProposalRunResponse:
        with Session(self.engine) as session:
            run = self._load_run(session, run_id)
            if run.safe_batch_approved:
                return self.get_run(run_id)
            for item in run.items:
                if not item.review_required and item.status == "READY":
                    item.status = "APPROVED"
            run.safe_batch_approved = True
            run.status = "IN_REVIEW" if run.exception_count else "REVIEWED"
            self._audit(session, run.id, "SAFE_BATCH_APPROVED", {
                "proposal_ids": [item.stable_key for item in run.items if not item.review_required],
            })
            session.commit()
        return self.get_run(run_id)

    def review_item(
        self, run_id: str, item_id: str, decision: str, correction: dict[str, Any], note: str | None
    ) -> ProposalRunResponse:
        with Session(self.engine) as session:
            run = self._load_run(session, run_id)
            item = next((candidate for candidate in run.items if candidate.id == item_id), None)
            if item is None:
                raise KeyError(item_id)
            if not item.review_required:
                raise ValueError("Safe proposals are approved globally")
            normalized = decision.upper()
            statuses = {
                "APPROVE": "APPROVED",
                "CORRECT": "CORRECTED",
                "REJECT": "REJECTED",
                "KEEP_UNCHANGED": "KEPT",
            }
            if normalized not in statuses:
                raise ValueError("Unsupported review decision")
            if normalized == "CORRECT":
                self._validate_correction(run.semantic_run, item, correction)
            review = UserReview(
                proposal_run_id=run.id,
                proposal_item_id=item.id,
                decision=normalized,
                correction_json=json.dumps(correction, ensure_ascii=False, sort_keys=True),
                note=note,
            )
            session.add(review)
            item.status = statuses[normalized]
            unresolved = sum(
                candidate.review_required and candidate.id != item.id and candidate.status == "PENDING_REVIEW"
                for candidate in run.items
            )
            run.status = "REVIEWED" if unresolved == 0 and run.safe_batch_approved else "IN_REVIEW"
            self._audit(session, run.id, "USER_REVIEW_RECORDED", {
                "proposal_id": item.stable_key,
                "decision": normalized,
                "correction": correction,
            })
            session.commit()
        return self.get_run(run_id)

    def preview(self, run_id: str) -> PreviewResponse:
        with Session(self.engine) as session:
            run = self._load_run(session, run_id)
            before = self._current_state(session, run.semantic_run)
            proposed, applied_ids = self._build_proposed_state(run)
            unresolved = [item.stable_key for item in run.items if item.review_required and item.status == "PENDING_REVIEW"]
            before_hash = _state_hash(before)
            proposed_hash = _state_hash(proposed)
            self._audit(session, run.id, "PREVIEW_GENERATED", {
                "before_hash": before_hash,
                "proposed_hash": proposed_hash,
                "approved_proposal_ids": applied_ids,
                "unresolved_exception_ids": unresolved,
            })
            session.commit()
        return PreviewResponse(
            proposal_run_id=run_id,
            before_state=WorkspaceStateResponse(**before),
            proposed_state=WorkspaceStateResponse(**proposed),
            before_hash=before_hash,
            proposed_hash=proposed_hash,
            approved_proposal_ids=applied_ids,
            unresolved_exception_ids=unresolved,
            originals_modified=False,
        )

    def apply(self, run_id: str) -> AppliedOperationResponse:
        with Session(self.engine) as session:
            run = self._load_run(session, run_id)
            if not run.safe_batch_approved:
                raise ValueError("Safe proposal batch must be approved before applying")
            active = session.scalar(
                select(AppliedOperation).where(
                    AppliedOperation.proposal_run_id == run.id,
                    AppliedOperation.status == "APPLIED",
                )
            )
            if active is not None:
                raise ValueError("Proposal run already has an active applied operation")
            before = self._current_state(session, run.semantic_run)
            after, applied_ids = self._build_proposed_state(run)
            if not applied_ids:
                raise ValueError("No approved proposals to apply")
            before_hash = _state_hash(before)
            after_hash = _state_hash(after)
            operation = AppliedOperation(
                proposal_run_id=run.id,
                status="APPLIED",
                before_state_json=_canonical_json(before),
                after_state_json=_canonical_json(after),
                before_hash=before_hash,
                after_hash=after_hash,
                applied_proposal_ids_json=json.dumps(applied_ids, ensure_ascii=False),
                originals_modified=False,
            )
            session.add(operation)
            session.flush()
            workspace = session.scalar(select(WorkspaceState).where(WorkspaceState.semantic_run_id == run.semantic_run_id))
            if workspace is None:
                workspace = WorkspaceState(
                    semantic_run_id=run.semantic_run_id,
                    state_json=_canonical_json(after),
                    state_hash=after_hash,
                    revision=1,
                )
                session.add(workspace)
            else:
                workspace.state_json = _canonical_json(after)
                workspace.state_hash = after_hash
                workspace.revision += 1
                workspace.updated_at = datetime.now(timezone.utc)
            for item in run.items:
                if item.status in {"APPROVED", "CORRECTED"}:
                    item.status = "APPLIED"
            run.status = "APPLIED"
            run.completed_at = datetime.now(timezone.utc)
            self._audit(session, run.id, "OPERATIONS_APPLIED", {
                "operation_id": operation.id,
                "before_hash": before_hash,
                "after_hash": after_hash,
                "applied_proposal_ids": applied_ids,
                "originals_modified": False,
            }, operation.id)
            session.commit()
            operation_id = operation.id
        return self.get_operation(operation_id)

    def undo(self, operation_id: str) -> UndoOperationResponse:
        with Session(self.engine) as session:
            operation = session.scalar(
                select(AppliedOperation)
                .where(AppliedOperation.id == operation_id)
                .options(selectinload(AppliedOperation.proposal_run))
            )
            if operation is None:
                raise KeyError(operation_id)
            if operation.status != "APPLIED":
                raise ValueError("Only an active applied operation can be undone")
            workspace = session.scalar(
                select(WorkspaceState).where(
                    WorkspaceState.semantic_run_id == operation.proposal_run.semantic_run_id
                )
            )
            if workspace is None or workspace.state_hash != operation.after_hash:
                raise ValueError("Workspace state no longer matches the applied operation")
            restored = _loads(operation.before_state_json, {})
            restored_hash = _state_hash(restored)
            if restored_hash != operation.before_hash:
                raise RuntimeError("Stored before-state hash is invalid")
            workspace.state_json = _canonical_json(restored)
            workspace.state_hash = restored_hash
            workspace.revision += 1
            workspace.updated_at = datetime.now(timezone.utc)
            undo = UndoOperation(
                applied_operation_id=operation.id,
                status="COMPLETED",
                restored_state_json=_canonical_json(restored),
                restored_hash=restored_hash,
                audit_history_preserved=True,
                originals_modified=False,
            )
            session.add(undo)
            operation.status = "UNDONE"
            operation.undone_at = datetime.now(timezone.utc)
            operation.proposal_run.status = "UNDONE"
            self._audit(session, operation.proposal_run_id, "UNDO_EXECUTED", {
                "operation_id": operation.id,
                "restored_hash": restored_hash,
                "audit_history_preserved": True,
                "originals_modified": False,
            }, operation.id)
            session.commit()
            undo_id = undo.id
        return self.get_undo(undo_id)

    def list_runs(self) -> list[ProposalRunSummaryResponse]:
        with Session(self.engine) as session:
            runs = list(session.scalars(select(ProposalRun).order_by(ProposalRun.created_at.desc())).all())
            return [self._summary(run) for run in runs]

    def get_run(self, run_id: str) -> ProposalRunResponse:
        with Session(self.engine) as session:
            run = self._load_run(session, run_id)
            summary = self._summary(run)
            return ProposalRunResponse(**summary.model_dump(), items=[self._item(item) for item in sorted(run.items, key=lambda x: x.sort_order)])

    def get_operation(self, operation_id: str) -> AppliedOperationResponse:
        with Session(self.engine) as session:
            operation = session.get(AppliedOperation, operation_id)
            if operation is None:
                raise KeyError(operation_id)
            return AppliedOperationResponse(
                id=operation.id,
                proposal_run_id=operation.proposal_run_id,
                status=operation.status,
                before_hash=operation.before_hash,
                after_hash=operation.after_hash,
                applied_proposal_ids=_loads(operation.applied_proposal_ids_json, []),
                applied_at=operation.applied_at,
                undone_at=operation.undone_at,
                state=WorkspaceStateResponse(**_loads(operation.after_state_json, {})),
                originals_modified=operation.originals_modified,
            )

    def get_undo(self, undo_id: str) -> UndoOperationResponse:
        with Session(self.engine) as session:
            undo = session.get(UndoOperation, undo_id)
            if undo is None:
                raise KeyError(undo_id)
            return UndoOperationResponse(
                id=undo.id,
                applied_operation_id=undo.applied_operation_id,
                status=undo.status,
                restored_hash=undo.restored_hash,
                created_at=undo.created_at,
                audit_history_preserved=undo.audit_history_preserved,
                originals_modified=undo.originals_modified,
                state=WorkspaceStateResponse(**_loads(undo.restored_state_json, {})),
            )

    def audit(self, run_id: str) -> list[AuditEventResponse]:
        with Session(self.engine) as session:
            if session.get(ProposalRun, run_id) is None:
                raise KeyError(run_id)
            events = list(session.scalars(
                select(AuditEvent).where(AuditEvent.proposal_run_id == run_id).order_by(AuditEvent.sequence)
            ).all())
            return [AuditEventResponse(
                id=event.id,
                sequence=event.sequence,
                event_type=event.event_type,
                payload=_loads(event.payload_json, {}),
                applied_operation_id=event.applied_operation_id,
                created_at=event.created_at,
            ) for event in events]

    def _load_semantic(self, session: Session, run_id: str) -> SemanticRun:
        run = session.scalar(
            select(SemanticRun).where(SemanticRun.id == run_id).options(
                selectinload(SemanticRun.projects).selectinload(Project.memberships).selectinload(ProjectMembership.chat),
                selectinload(SemanticRun.projects).selectinload(Project.evidences),
                selectinload(SemanticRun.exceptions).selectinload(SemanticException.chat),
                selectinload(SemanticRun.analysis_run),
            )
        )
        if run is None:
            raise KeyError(run_id)
        return run

    def _load_run(self, session: Session, run_id: str) -> ProposalRun:
        run = session.scalar(
            select(ProposalRun).where(ProposalRun.id == run_id).options(
                selectinload(ProposalRun.items).selectinload(ProposalItem.reviews),
                selectinload(ProposalRun.semantic_run).selectinload(SemanticRun.projects).selectinload(Project.memberships).selectinload(ProjectMembership.chat),
                selectinload(ProposalRun.semantic_run).selectinload(SemanticRun.exceptions).selectinload(SemanticException.chat),
                selectinload(ProposalRun.semantic_run).selectinload(SemanticRun.analysis_run),
            )
        )
        if run is None:
            raise KeyError(run_id)
        return run

    def _fixture_items(self) -> list[dict[str, Any]]:
        path = self.settings.demo_data_dir / "expected_proposals.json"
        return json.loads(path.read_text(encoding="utf-8"))["proposal_items"]

    def _derive_items(self, semantic: SemanticRun) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        index = 1
        for project in sorted(semantic.projects, key=lambda item: item.project_key):
            items.append({
                "id": f"LIVE-{index:03d}", "operation": "CREATE_PROJECT",
                "target_ids": [project.project_key],
                "chat_ids": [m.chat.external_id for m in project.memberships if m.status == "CONFIRMADA"],
                "confidence": project.confidence, "review_required": False,
                "evidence_ids": [e.id for e in project.evidences],
                "reason": "Project and operational memory reconstructed from semantic evidence.",
            })
            index += 1
        for chat_id in _loads(semantic.independent_chat_ids_json, []):
            items.append({
                "id": f"LIVE-{index:03d}", "operation": "KEEP_INDEPENDENT",
                "target_ids": [chat_id], "confidence": "ALTA", "review_required": False,
                "evidence_ids": [], "reason": "One-off conversation without project continuity.",
            })
            index += 1
        for exception in semantic.exceptions:
            items.append({
                "id": f"LIVE-{index:03d}", "operation": exception.kind,
                "target_ids": [exception.chat.external_id] if exception.chat else [],
                "candidate_project_ids": _loads(exception.candidate_project_keys_json, []),
                "confidence": exception.confidence, "review_required": True,
                "evidence_ids": [], "reason": exception.reason,
            })
            index += 1
        return items

    def _current_state(self, session: Session, semantic: SemanticRun) -> dict[str, Any]:
        workspace = session.scalar(select(WorkspaceState).where(WorkspaceState.semantic_run_id == semantic.id))
        if workspace is not None:
            return _loads(workspace.state_json, {})
        batch_id = semantic.analysis_run.batch_id
        chat_ids = list(session.scalars(select(Chat.external_id).where(Chat.batch_id == batch_id).order_by(Chat.external_id)).all())
        return {
            "semantic_run_id": semantic.id,
            "projects": [],
            "exact_duplicates": [],
            "partial_duplicates": [],
            "independent_chat_ids": [],
            "unclassified_chat_ids": chat_ids,
            "protected_chat_ids": [],
            "originals_modified": False,
        }

    def _build_proposed_state(self, run: ProposalRun) -> tuple[dict[str, Any], list[str]]:
        applicable = [item for item in run.items if item.status in APPLICABLE_STATUSES]
        applied_ids = [item.stable_key for item in sorted(applicable, key=lambda x: x.sort_order)]
        item_by_op: dict[str, list[ProposalItem]] = {}
        for item in applicable:
            item_by_op.setdefault(item.operation, []).append(item)

        exact_duplicates = []
        duplicate_ids: set[str] = set()
        for item in item_by_op.get("MARK_EXACT_DUPLICATE", []):
            payload = _loads(item.payload_json, {})
            target = _loads(item.target_ids_json, [])
            if target:
                duplicate_ids.add(target[0])
                exact_duplicates.append({"duplicate_chat_id": target[0], "canonical_chat_id": payload.get("canonical_chat_id")})

        created_keys = {
            target
            for item in item_by_op.get("CREATE_PROJECT", [])
            for target in _loads(item.target_ids_json, [])
        }
        state_overrides: dict[str, str] = {}
        for item in item_by_op.get("SET_PROJECT_STATE", []):
            payload = _loads(item.payload_json, {})
            for target in _loads(item.target_ids_json, []):
                if payload.get("state"):
                    state_overrides[target] = payload["state"]

        projects: list[dict[str, Any]] = []
        project_map: dict[str, dict[str, Any]] = {}
        for project in sorted(run.semantic_run.projects, key=lambda item: item.project_key):
            if project.project_key not in created_keys:
                continue
            memberships = sorted({
                membership.chat.external_id
                for membership in project.memberships
                if membership.status == "CONFIRMADA" and membership.chat.external_id not in duplicate_ids
            })
            row = {
                "project_key": project.project_key,
                "name": project.name,
                "state": state_overrides.get(project.project_key, project.state),
                "current_version": project.current_version,
                "previous_versions": _loads(project.previous_versions_json, []),
                "discarded_versions": _loads(project.discarded_versions_json, []),
                "pending_tasks": _loads(project.pending_tasks_json, []),
                "memberships": memberships,
            }
            projects.append(row)
            project_map[project.project_key] = row

        unresolved: set[str] = set()
        rejected_or_kept: set[str] = set()
        for item in run.items:
            if not item.review_required:
                continue
            targets = _loads(item.target_ids_json, [])
            review = max(item.reviews, key=lambda value: value.created_at) if item.reviews else None
            if item.status == "PENDING_REVIEW":
                unresolved.update(targets)
                continue
            if item.status in {"REJECTED", "KEPT"}:
                rejected_or_kept.update(targets)
            if item.status in {"CORRECTED", "APPLIED"} and review and review.decision == "CORRECT":
                correction = _loads(review.correction_json, {})
                key = correction.get("project_key")
                if key in project_map:
                    for target in targets:
                        if target not in duplicate_ids and target not in project_map[key]["memberships"]:
                            project_map[key]["memberships"].append(target)
                            project_map[key]["memberships"].sort()

        partial_duplicates = []
        for item in item_by_op.get("MARK_PARTIAL_DUPLICATE", []):
            payload = _loads(item.payload_json, {})
            target = _loads(item.target_ids_json, [])
            if target:
                partial_duplicates.append({
                    "chat_id": target[0],
                    "canonical_chat_id": payload.get("canonical_chat_id"),
                    "merged": False,
                })

        independent = sorted({
            target
            for item in item_by_op.get("KEEP_INDEPENDENT", [])
            for target in _loads(item.target_ids_json, [])
        })
        unclassified = set(_loads(run.semantic_run.unclassified_chat_ids_json, []))
        unclassified.update(rejected_or_kept)

        return ({
            "semantic_run_id": run.semantic_run_id,
            "projects": projects,
            "exact_duplicates": sorted(exact_duplicates, key=lambda row: row["duplicate_chat_id"]),
            "partial_duplicates": sorted(partial_duplicates, key=lambda row: row["chat_id"]),
            "independent_chat_ids": independent,
            "unclassified_chat_ids": sorted(unclassified),
            "protected_chat_ids": sorted(unresolved),
            "originals_modified": False,
        }, applied_ids)

    def _validate_correction(self, semantic: SemanticRun, item: ProposalItem, correction: dict[str, Any]) -> None:
        if not correction:
            raise ValueError("A correction payload is required")
        project_key = correction.get("project_key")
        if item.operation == "REVIEW_MEMBERSHIP" or project_key is not None:
            available = {project.project_key for project in semantic.projects}
            if project_key not in available:
                raise ValueError("Correction project_key is not part of the semantic run")

    def _summary(self, run: ProposalRun) -> ProposalRunSummaryResponse:
        reviewed = sum(item.review_required and item.status != "PENDING_REVIEW" for item in run.items)
        unresolved = sum(item.review_required and item.status == "PENDING_REVIEW" for item in run.items)
        return ProposalRunSummaryResponse(
            id=run.id, semantic_run_id=run.semantic_run_id, status=run.status,
            created_at=run.created_at, completed_at=run.completed_at,
            safe_count=run.safe_count, exception_count=run.exception_count,
            safe_batch_approved=run.safe_batch_approved,
            reviewed_exception_count=reviewed, unresolved_exception_count=unresolved,
            originals_modified=run.originals_modified,
        )

    def _item(self, item: ProposalItem) -> ProposalItemResponse:
        latest = max(item.reviews, key=lambda value: value.created_at) if item.reviews else None
        review = None if latest is None else UserReviewResponse(
            id=latest.id, decision=latest.decision,
            correction=_loads(latest.correction_json, {}), note=latest.note, created_at=latest.created_at,
        )
        return ProposalItemResponse(
            id=item.id, stable_key=item.stable_key, operation=item.operation, title=item.title,
            reason=item.reason, confidence=item.confidence, review_required=item.review_required,
            status=item.status, target_ids=_loads(item.target_ids_json, []),
            candidate_project_keys=_loads(item.candidate_project_keys_json, []),
            evidence_ids=_loads(item.evidence_ids_json, []), payload=_loads(item.payload_json, {}),
            latest_review=review,
        )

    def _audit(
        self, session: Session, run_id: str, event_type: str, payload: dict[str, Any], operation_id: str | None = None
    ) -> None:
        max_sequence = session.scalar(select(func.max(AuditEvent.sequence)).where(AuditEvent.proposal_run_id == run_id)) or 0
        session.add(AuditEvent(
            proposal_run_id=run_id, applied_operation_id=operation_id,
            sequence=max_sequence + 1, event_type=event_type,
            payload_json=json.dumps(payload, ensure_ascii=False, sort_keys=True),
        ))

    @staticmethod
    def _title(operation: str, targets: list[str]) -> str:
        labels = {
            "CREATE_PROJECT": "Create detected project",
            "MARK_EXACT_DUPLICATE": "Mark exact duplicate",
            "MARK_PARTIAL_DUPLICATE": "Record partial duplicate without merging",
            "MARK_PREVIOUS_VERSION": "Mark previous version",
            "MARK_DISCARDED_VERSION": "Mark discarded version",
            "SET_PROJECT_STATE": "Set project lifecycle state",
            "KEEP_INDEPENDENT": "Keep conversations independent",
            "KEEP_UNCLASSIFIED": "Keep conversation unclassified",
            "REVIEW_MEMBERSHIP": "Resolve ambiguous project membership",
        }
        suffix = f" · {', '.join(targets)}" if targets else ""
        return labels.get(operation, operation.replace("_", " ").title()) + suffix

from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import combinations
from typing import Any, Iterable

from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Chat, ImportBatch, Message
from app.models.analysis_evidence import AnalysisEvidence
from app.models.analysis_finding import AnalysisFinding
from app.models.analysis_run import AnalysisRun

ENGINE_VERSION = "deterministic-ot010-v1"
CONFIDENCE_VALUES = {"ALTA", "MEDIA", "BAJA"}
VERSION_RE = re.compile(r"\b[vV]\s?\d+(?:\.\d+)*\b")
SEMVER_RE = re.compile(r"\b\d+\.\d+\.\d+\b")
WORD_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "que", "con", "para", "por", "del", "las", "los", "una", "uno", "unos", "unas",
    "esta", "este", "esto", "como", "pero", "cuando", "desde", "hasta", "solo", "sigue",
    "queda", "quedar", "debe", "deben", "puede", "podria", "podriamos", "mas", "bien", "correctamente",
    "version", "proyecto", "fase", "actual", "nueva", "futura", "final", "prueba", "crear", "mejorar",
}
STATE_ENTITY_STOPWORDS = STOPWORDS | {
    "activo", "cerrado", "cerrar", "terminado", "pausa", "pausamos", "pendiente", "archivado", "archivada",
    "sigue", "permanece", "despliegue", "considerarse", "queda",
}


@dataclass(frozen=True)
class EvidenceView:
    id: str
    kind: str
    quote: str
    precedence: int
    occurred_at: datetime | None
    chat_external_id: str
    message_external_id: str | None


@dataclass(frozen=True)
class FindingView:
    id: str
    stable_key: str
    finding_type: str
    subject: str
    classification: str | None
    confidence: str
    chat_external_id: str | None
    related_chat_external_id: str | None
    details: dict[str, Any]
    evidences: list[EvidenceView]


@dataclass(frozen=True)
class AnalysisRunView:
    id: str
    batch_id: str
    engine_version: str
    status: str
    created_at: datetime
    completed_at: datetime | None
    chat_count: int
    finding_count: int
    evidence_count: int
    exact_duplicate_count: int
    partial_duplicate_count: int
    version_count: int
    decision_count: int
    task_count: int
    state_signal_count: int
    originals_modified: bool
    findings: list[FindingView]


@dataclass(frozen=True)
class FindingDraft:
    stable_key: str
    finding_type: str
    subject: str
    classification: str | None
    confidence: str
    chat: Chat | None
    related_chat: Chat | None
    details: dict[str, Any]
    evidence_specs: list[tuple[Chat, Message | None, str, str, int, datetime | None]]


@dataclass(frozen=True)
class StateSignal:
    chat: Chat
    message: Message
    state: str
    confidence: str
    precedence: int
    occurred_at: datetime | None


class AnalysisService:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def run(self, batch_id: str) -> AnalysisRunView:
        with Session(self.engine) as session:
            batch = session.get(ImportBatch, batch_id)
            if batch is None:
                raise KeyError(batch_id)
            if batch.status not in {"COMPLETED", "COMPLETED_WITH_ERRORS"}:
                raise ValueError("Import batch must be completed before analysis")
            chats = list(
                session.scalars(
                    select(Chat)
                    .where(Chat.batch_id == batch_id)
                    .order_by(Chat.created_at, Chat.external_id)
                    .options(selectinload(Chat.messages))
                ).all()
            )
            if not chats:
                raise ValueError("Import batch has no normalized chats")

            run = AnalysisRun(batch_id=batch_id, engine_version=ENGINE_VERSION, chat_count=len(chats))
            session.add(run)
            session.flush()
            run_id = run.id
            try:
                drafts = self._analyze(chats)
                evidence_cache: dict[tuple[str, str | None, str, str, int], AnalysisEvidence] = {}
                for draft in drafts:
                    if draft.confidence not in CONFIDENCE_VALUES:
                        raise RuntimeError(f"Invalid confidence: {draft.confidence}")
                    finding = AnalysisFinding(
                        run_id=run.id,
                        stable_key=draft.stable_key,
                        finding_type=draft.finding_type,
                        subject=draft.subject,
                        classification=draft.classification,
                        confidence=draft.confidence,
                        chat_id=draft.chat.id if draft.chat else None,
                        related_chat_id=draft.related_chat.id if draft.related_chat else None,
                        details_json=json.dumps(draft.details, ensure_ascii=False, sort_keys=True),
                    )
                    session.add(finding)
                    for chat, message, kind, quote, precedence, occurred_at in draft.evidence_specs:
                        key = (chat.id, message.id if message else None, kind, quote, precedence)
                        evidence = evidence_cache.get(key)
                        if evidence is None:
                            evidence = AnalysisEvidence(
                                run_id=run.id,
                                chat_id=chat.id,
                                message_id=message.id if message else None,
                                kind=kind,
                                quote=quote,
                                precedence=precedence,
                                occurred_at=occurred_at,
                            )
                            session.add(evidence)
                            evidence_cache[key] = evidence
                        finding.evidences.append(evidence)

                run.finding_count = len(drafts)
                run.evidence_count = len(evidence_cache)
                run.exact_duplicate_count = sum(d.finding_type == "EXACT_DUPLICATE" for d in drafts)
                run.partial_duplicate_count = sum(d.finding_type == "PARTIAL_DUPLICATE" for d in drafts)
                run.version_count = sum(d.finding_type == "VERSION_STATUS" for d in drafts)
                run.decision_count = sum(d.finding_type == "DECISION" for d in drafts)
                run.task_count = sum(d.finding_type == "TASK" for d in drafts)
                run.state_signal_count = sum(d.finding_type in {"STATE_SIGNAL", "STATE_PRECEDENCE"} for d in drafts)
                run.status = "COMPLETED"
                run.completed_at = datetime.now(timezone.utc)
                run.originals_modified = False
                session.commit()
            except Exception:
                session.rollback()
                with Session(self.engine) as recovery:
                    failed = recovery.get(AnalysisRun, run.id)
                    if failed is not None:
                        failed.status = "FAILED"
                        failed.completed_at = datetime.now(timezone.utc)
                        recovery.commit()
                raise
        return self.get_run(run_id)

    def _analyze(self, chats: list[Chat]) -> list[FindingDraft]:
        drafts: list[FindingDraft] = []
        exact, duplicate_ids = self._exact_duplicates(chats)
        drafts.extend(exact)
        canonical_chats = [chat for chat in chats if chat.id not in duplicate_ids]
        drafts.extend(self._partial_duplicates(canonical_chats))
        drafts.extend(self._version_findings(canonical_chats))
        drafts.extend(self._decision_findings(canonical_chats))
        drafts.extend(self._task_findings(canonical_chats))
        state_drafts, signals = self._state_findings(canonical_chats)
        drafts.extend(state_drafts)
        drafts.extend(self._state_precedence(signals))
        return sorted(drafts, key=lambda item: (item.finding_type, item.stable_key))

    def _exact_duplicates(self, chats: list[Chat]) -> tuple[list[FindingDraft], set[str]]:
        groups: dict[str, list[Chat]] = defaultdict(list)
        for chat in chats:
            groups[chat.content_fingerprint].append(chat)
        drafts: list[FindingDraft] = []
        duplicate_ids: set[str] = set()
        for fingerprint, group in sorted(groups.items()):
            if len(group) < 2:
                continue
            ordered = sorted(group, key=lambda chat: (self._time_key(chat.created_at), chat.external_id))
            canonical = ordered[0]
            for duplicate in ordered[1:]:
                duplicate_ids.add(duplicate.id)
                drafts.append(
                    FindingDraft(
                        stable_key=f"exact_duplicate:{duplicate.external_id}:{canonical.external_id}",
                        finding_type="EXACT_DUPLICATE",
                        subject=duplicate.title,
                        classification="EXACT_DUPLICATE",
                        confidence="ALTA",
                        chat=duplicate,
                        related_chat=canonical,
                        details={"similarity": 1.0, "fingerprint": fingerprint, "canonical_chat": canonical.external_id},
                        evidence_specs=[
                            (canonical, None, "EXACT_DUPLICATE", f"Normalized fingerprint {fingerprint}", 4, canonical.updated_at),
                            (duplicate, None, "EXACT_DUPLICATE", f"Normalized fingerprint {fingerprint}", 4, duplicate.updated_at),
                        ],
                    )
                )
        return drafts, duplicate_ids

    def _partial_duplicates(self, chats: list[Chat]) -> list[FindingDraft]:
        drafts: list[FindingDraft] = []
        token_map = {chat.id: self._chat_tokens(chat) for chat in chats}
        for left, right in combinations(chats, 2):
            left_tokens, right_tokens = token_map[left.id], token_map[right.id]
            if not left_tokens or not right_tokens:
                continue
            intersection = left_tokens & right_tokens
            union = left_tokens | right_tokens
            jaccard = len(intersection) / len(union)
            coverage = max(len(intersection) / len(left_tokens), len(intersection) / len(right_tokens))
            if len(intersection) < 5 or jaccard < 0.35 or coverage < 0.65:
                continue
            first, second = sorted((left, right), key=lambda chat: chat.external_id)
            drafts.append(
                FindingDraft(
                    stable_key=f"partial_duplicate:{first.external_id}:{second.external_id}",
                    finding_type="PARTIAL_DUPLICATE",
                    subject=f"{first.title} ↔ {second.title}",
                    classification="REVIEW_REQUIRED",
                    confidence="MEDIA",
                    chat=second,
                    related_chat=first,
                    details={
                        "jaccard": round(jaccard, 4),
                        "coverage": round(coverage, 4),
                        "shared_terms": sorted(intersection),
                        "automatic_merge": False,
                    },
                    evidence_specs=[
                        (first, None, "PARTIAL_DUPLICATE", self._chat_excerpt(first), 7, first.updated_at),
                        (second, None, "PARTIAL_DUPLICATE", self._chat_excerpt(second), 7, second.updated_at),
                    ],
                )
            )
        return drafts

    def _version_findings(self, chats: list[Chat]) -> list[FindingDraft]:
        occurrences: dict[str, list[tuple[Chat, Message, str, int, str, datetime | None]]] = defaultdict(list)
        for chat in chats:
            last_versions: set[str] = set()
            for message in chat.messages:
                explicit_versions = {self._normalize_version(item) for item in VERSION_RE.findall(message.content)}
                if "version" in self._fold(message.content):
                    explicit_versions.update(SEMVER_RE.findall(message.content))
                versions = explicit_versions
                folded = self._fold(message.content)
                if not versions and last_versions and any(marker in folded for marker in ("esta version", "la version", "esa version")):
                    versions = set(last_versions)
                for version in versions:
                    context = self._version_context(message.content, version) if version in explicit_versions else message.content
                    status, precedence = self._version_status(context)
                    occurrences[version].append(
                        (chat, message, status, precedence, message.content, message.timestamp or chat.updated_at)
                    )
                if explicit_versions:
                    last_versions = explicit_versions

        drafts: list[FindingDraft] = []
        for version, items in sorted(occurrences.items()):
            explicit = [item for item in items if item[2] != "UNRESOLVED"]
            candidates = explicit or items
            chosen = max(
                candidates,
                key=lambda item: (
                    self._time_key(item[5]),
                    -item[3],
                    item[1].position,
                    item[0].external_id,
                ),
            )
            classification = chosen[2]
            confidence = "ALTA" if chosen[3] <= 2 else "MEDIA" if chosen[3] <= 5 else "BAJA"
            evidences = [
                (chat, message, "VERSION_REFERENCE", quote, precedence, occurred_at)
                for chat, message, _status, precedence, quote, occurred_at in sorted(
                    items, key=lambda item: (self._time_key(item[5]), item[1].position, item[0].external_id)
                )
            ]
            drafts.append(
                FindingDraft(
                    stable_key=f"version:{version}",
                    finding_type="VERSION_STATUS",
                    subject=version,
                    classification=classification,
                    confidence=confidence,
                    chat=chosen[0],
                    related_chat=None,
                    details={
                        "resolution": "latest explicit evidence",
                        "occurrences": len(items),
                        "chosen_chat": chosen[0].external_id,
                    },
                    evidence_specs=evidences,
                )
            )
        return drafts

    def _decision_findings(self, chats: list[Chat]) -> list[FindingDraft]:
        drafts: list[FindingDraft] = []
        for chat in chats:
            for message in chat.messages:
                folded = self._fold(message.content)
                classification: str | None = None
                precedence = 8
                confidence = "BAJA"
                if any(marker in folded for marker in (
                    "queda aprobada", "queda aprobado", "fase aprobada", "base oficial", "base vigente",
                    "queda validada", "queda validado", "esta instalada y validada", "esta probado y funciona",
                )):
                    classification, precedence, confidence = "APPROVED", 2, "ALTA"
                elif any(marker in folded for marker in (
                    "queda descartada", "se descartan", "se rechaza", "no usar", "no crear ni proponer",
                    "queda no validada", "no queda estable",
                )):
                    classification, precedence, confidence = "DISCARDED", 1, "ALTA"
                elif any(marker in folded for marker in ("no implementarlo todavia", "para una fase futura", "fase posterior")):
                    classification, precedence, confidence = "DEFERRED", 5, "MEDIA"
                elif "no debe cerrarse" in folded:
                    classification, precedence, confidence = "REPLACED", 1, "ALTA"
                if classification is None:
                    continue
                drafts.append(
                    FindingDraft(
                        stable_key=f"decision:{chat.external_id}:{message.position}:{classification.lower()}",
                        finding_type="DECISION",
                        subject=self._compact(message.content),
                        classification=classification,
                        confidence=confidence,
                        chat=chat,
                        related_chat=None,
                        details={"role": message.role},
                        evidence_specs=[(chat, message, "DECISION", message.content, precedence, message.timestamp or chat.updated_at)],
                    )
                )
        return drafts

    def _task_findings(self, chats: list[Chat]) -> list[FindingDraft]:
        drafts: list[FindingDraft] = []
        for chat in chats:
            for message in chat.messages:
                folded = self._fold(message.content)
                confidence: str | None = None
                precedence = 8
                if any(marker in folded for marker in ("queda pendiente", "sigue pendiente", "tareas pendientes")):
                    confidence, precedence = "ALTA", 5
                elif any(marker in folded for marker in (
                    "proxima fase aprobada", "fase futura", "fase posterior", "hasta revisar", "hay que mejorar",
                    "debe separarse", "queda aprobada una futura",
                )):
                    confidence, precedence = "MEDIA", 6
                elif any(marker in folded for marker in ("mas adelante", "mejorarlo", "retomarlo")):
                    confidence, precedence = "BAJA", 7
                if confidence is None:
                    continue
                drafts.append(
                    FindingDraft(
                        stable_key=f"task:{chat.external_id}:{message.position}",
                        finding_type="TASK",
                        subject=self._compact(message.content),
                        classification="PENDING",
                        confidence=confidence,
                        chat=chat,
                        related_chat=None,
                        details={"automatic_execution": False},
                        evidence_specs=[(chat, message, "TASK", message.content, precedence, message.timestamp or chat.updated_at)],
                    )
                )
        return drafts

    def _state_findings(self, chats: list[Chat]) -> tuple[list[FindingDraft], list[StateSignal]]:
        grouped: dict[tuple[str, str], list[StateSignal]] = defaultdict(list)
        for chat in chats:
            for message in chat.messages:
                folded = self._fold(message.content)
                state: str | None = None
                confidence = "BAJA"
                precedence = 8
                if "en_pausa" in folded or "pausamos" in folded:
                    state, confidence, precedence = "EN_PAUSA", "ALTA", 1
                elif "queda archivada" in folded or "iniciativa de voz queda archivada" in folded:
                    state, confidence, precedence = "ARCHIVADO", "ALTA", 1
                elif "proyecto permanece activo" in folded or "sigue en uso" in folded:
                    state, confidence, precedence = "ACTIVO", "ALTA", 1
                elif "proyecto pendiente" in folded:
                    state, confidence, precedence = "PENDIENTE", "ALTA", 1
                elif "proyecto puede considerarse terminado" in folded:
                    state, confidence, precedence = "CERRADO", "ALTA", 1
                elif "podriamos dar por cerrado" in folded:
                    state, confidence, precedence = "CERRADO", "BAJA", 7
                if state is None:
                    continue
                occurred_at = message.timestamp or chat.updated_at or chat.created_at
                grouped[(chat.id, state)].append(
                    StateSignal(chat, message, state, confidence, precedence, occurred_at)
                )

        drafts: list[FindingDraft] = []
        signals: list[StateSignal] = []
        for (_chat_id, state), items in sorted(grouped.items(), key=lambda item: (item[1][0].chat.external_id, item[0][1])):
            representative = max(
                items,
                key=lambda item: (self._time_key(item.occurred_at), -item.precedence, item.message.position),
            )
            confidence = "ALTA" if any(item.confidence == "ALTA" for item in items) else representative.confidence
            precedence = min(item.precedence for item in items)
            occurred_at = max(items, key=lambda item: self._time_key(item.occurred_at)).occurred_at
            signal = StateSignal(
                representative.chat,
                representative.message,
                state,
                confidence,
                precedence,
                occurred_at,
            )
            signals.append(signal)
            drafts.append(
                FindingDraft(
                    stable_key=f"state:{representative.chat.external_id}:{state.lower()}",
                    finding_type="STATE_SIGNAL",
                    subject=representative.chat.title,
                    classification=state,
                    confidence=confidence,
                    chat=representative.chat,
                    related_chat=None,
                    details={"resolved_project_state": False, "evidence_count": len(items)},
                    evidence_specs=[
                        (
                            item.chat,
                            item.message,
                            "STATE_SIGNAL",
                            item.message.content,
                            item.precedence,
                            item.occurred_at,
                        )
                        for item in sorted(items, key=lambda item: (self._time_key(item.occurred_at), item.message.position))
                    ],
                )
            )
        return drafts, signals

    def _state_precedence(self, signals: list[StateSignal]) -> list[FindingDraft]:
        drafts: list[FindingDraft] = []
        seen_pairs: set[tuple[str, str]] = set()
        for left, right in combinations(signals, 2):
            if left.chat.id == right.chat.id or left.state == right.state:
                continue
            overlap = self._entity_tokens(left.chat) & self._entity_tokens(right.chat)
            if not overlap:
                continue
            older, newer = sorted(
                (left, right),
                key=lambda signal: (self._time_key(signal.occurred_at), signal.message.position, signal.chat.external_id),
            )
            if self._time_key(older.occurred_at) == self._time_key(newer.occurred_at):
                continue
            pair = (older.chat.id, newer.chat.id)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            confidence = "ALTA" if newer.confidence == "ALTA" else "MEDIA"
            drafts.append(
                FindingDraft(
                    stable_key=f"state_precedence:{older.chat.external_id}:{newer.chat.external_id}",
                    finding_type="STATE_PRECEDENCE",
                    subject=" / ".join(sorted(overlap)),
                    classification=newer.state,
                    confidence=confidence,
                    chat=newer.chat,
                    related_chat=older.chat,
                    details={
                        "previous_state": older.state,
                        "current_state": newer.state,
                        "rule": "latest explicit evidence",
                        "shared_entity_terms": sorted(overlap),
                    },
                    evidence_specs=[
                        (older.chat, older.message, "STATE_PRECEDENCE", older.message.content, older.precedence, older.occurred_at),
                        (newer.chat, newer.message, "STATE_PRECEDENCE", newer.message.content, newer.precedence, newer.occurred_at),
                    ],
                )
            )
        return drafts

    def list_runs(self, batch_id: str | None = None, limit: int = 20) -> list[AnalysisRun]:
        with Session(self.engine) as session:
            statement = select(AnalysisRun).order_by(AnalysisRun.created_at.desc()).limit(limit)
            if batch_id:
                statement = statement.where(AnalysisRun.batch_id == batch_id)
            return list(session.scalars(statement).all())

    def get_run(self, run_id: str) -> AnalysisRunView:
        with Session(self.engine) as session:
            run = session.scalar(
                select(AnalysisRun)
                .where(AnalysisRun.id == run_id)
                .options(
                    selectinload(AnalysisRun.findings).selectinload(AnalysisFinding.chat),
                    selectinload(AnalysisRun.findings).selectinload(AnalysisFinding.related_chat),
                    selectinload(AnalysisRun.findings).selectinload(AnalysisFinding.evidences).selectinload(AnalysisEvidence.chat),
                    selectinload(AnalysisRun.findings).selectinload(AnalysisFinding.evidences).selectinload(AnalysisEvidence.message),
                )
            )
            if run is None:
                raise KeyError(run_id)
            return self._run_view(run)

    def list_findings(
        self,
        run_id: str,
        finding_type: str | None,
        confidence: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[FindingView], int]:
        with Session(self.engine) as session:
            if session.get(AnalysisRun, run_id) is None:
                raise KeyError(run_id)
            filters = [AnalysisFinding.run_id == run_id]
            if finding_type:
                filters.append(AnalysisFinding.finding_type == finding_type)
            if confidence:
                filters.append(AnalysisFinding.confidence == confidence)
            total = session.scalar(select(func.count()).select_from(AnalysisFinding).where(*filters)) or 0
            findings = list(
                session.scalars(
                    select(AnalysisFinding)
                    .where(*filters)
                    .order_by(AnalysisFinding.finding_type, AnalysisFinding.stable_key)
                    .offset(offset)
                    .limit(limit)
                    .options(
                        selectinload(AnalysisFinding.chat),
                        selectinload(AnalysisFinding.related_chat),
                        selectinload(AnalysisFinding.evidences).selectinload(AnalysisEvidence.chat),
                        selectinload(AnalysisFinding.evidences).selectinload(AnalysisEvidence.message),
                    )
                ).all()
            )
            return [self._finding_view(item) for item in findings], total

    def _run_view(self, run: AnalysisRun) -> AnalysisRunView:
        return AnalysisRunView(
            id=run.id,
            batch_id=run.batch_id,
            engine_version=run.engine_version,
            status=run.status,
            created_at=run.created_at,
            completed_at=run.completed_at,
            chat_count=run.chat_count,
            finding_count=run.finding_count,
            evidence_count=run.evidence_count,
            exact_duplicate_count=run.exact_duplicate_count,
            partial_duplicate_count=run.partial_duplicate_count,
            version_count=run.version_count,
            decision_count=run.decision_count,
            task_count=run.task_count,
            state_signal_count=run.state_signal_count,
            originals_modified=run.originals_modified,
            findings=[self._finding_view(item) for item in sorted(run.findings, key=lambda item: (item.finding_type, item.stable_key))],
        )

    @staticmethod
    def _finding_view(finding: AnalysisFinding) -> FindingView:
        return FindingView(
            id=finding.id,
            stable_key=finding.stable_key,
            finding_type=finding.finding_type,
            subject=finding.subject,
            classification=finding.classification,
            confidence=finding.confidence,
            chat_external_id=finding.chat.external_id if finding.chat else None,
            related_chat_external_id=finding.related_chat.external_id if finding.related_chat else None,
            details=json.loads(finding.details_json),
            evidences=[
                EvidenceView(
                    id=evidence.id,
                    kind=evidence.kind,
                    quote=evidence.quote,
                    precedence=evidence.precedence,
                    occurred_at=evidence.occurred_at,
                    chat_external_id=evidence.chat.external_id,
                    message_external_id=evidence.message.external_id if evidence.message else None,
                )
                for evidence in sorted(
                    finding.evidences,
                    key=lambda item: (item.precedence, AnalysisService._time_key(item.occurred_at), item.chat.external_id),
                )
            ],
        )

    @staticmethod
    def _time_key(value: datetime | None) -> float:
        if value is None:
            return float("-inf")
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.timestamp()

    @classmethod
    def _version_context(cls, content: str, version: str) -> str:
        clauses = [clause.strip() for clause in re.split(r"[.;!?]+", content) if clause.strip()]
        folded_version = cls._fold(version).replace(" ", "")
        for clause in clauses:
            normalized_clause = cls._fold(clause).replace(" ", "")
            if folded_version in normalized_clause:
                return clause
        return content

    @classmethod
    def _version_status(cls, content: str) -> tuple[str, int]:
        folded = cls._fold(content)
        if any(marker in folded for marker in (
            "se descartan", "queda descartada", "se rechaza", "no validada", "no usar",
            "no queda estable", "sigue sin captar", "no capta correctamente",
        )):
            return "DISCARDED", 1
        if "version anterior" in folded or "como version anterior" in folded:
            return "PREVIOUS", 1
        if any(marker in folded for marker in (
            "version vigente", "base vigente", "base oficial", "version final estable",
            "queda validada", "queda validado", "instalada y validada",
        )):
            return "CURRENT", 2
        if any(marker in folded for marker in (
            "base estable", "esta funcionando", "esta probada y funciona", "funciona",
            "abre correctamente", "arranca bien", "escanea y envia correctamente",
        )):
            return "CURRENT", 4
        return "UNRESOLVED", 8

    @classmethod
    def _chat_tokens(cls, chat: Chat) -> set[str]:
        text = " ".join(message.content for message in chat.messages if message.role == "user")
        return {token for token in WORD_RE.findall(cls._fold(text)) if len(token) >= 3 and token not in STOPWORDS}

    @classmethod
    def _entity_tokens(cls, chat: Chat) -> set[str]:
        return {
            token for token in WORD_RE.findall(cls._fold(chat.title))
            if len(token) >= 4 and token not in STATE_ENTITY_STOPWORDS
        }

    @classmethod
    def _fold(cls, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.lower())
        return "".join(character for character in normalized if not unicodedata.combining(character))

    @classmethod
    def _normalize_version(cls, value: str) -> str:
        return re.sub(r"\s+", "", value).upper()

    @staticmethod
    def _compact(value: str, limit: int = 180) -> str:
        text = " ".join(value.split())
        return text if len(text) <= limit else f"{text[: limit - 1]}…"

    @classmethod
    def _chat_excerpt(cls, chat: Chat) -> str:
        return cls._compact(" ".join(message.content for message in chat.messages), 260)

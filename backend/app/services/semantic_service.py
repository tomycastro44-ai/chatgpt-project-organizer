from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.models import (
    AnalysisFinding,
    AnalysisRun,
    Chat,
    Project,
    ProjectEvidence,
    ProjectMembership,
    SemanticException,
    SemanticRun,
)
from app.schemas.semantic import (
    ProjectEvidenceResponse,
    ProjectMembershipResponse,
    ProjectResponse,
    SemanticCapabilityResponse,
    SemanticExceptionResponse,
    SemanticRunResponse,
    SemanticRunSummaryResponse,
)
from app.schemas.semantic_contracts import (
    SemanticAnalysisPayload,
    SemanticEvidencePayload,
    SemanticExceptionPayload,
    SemanticMembershipPayload,
    SemanticProjectPayload,
)

SEMANTIC_ENGINE_VERSION = "semantic-ot011-v1"
ALLOWED_STATES = {"ACTIVO", "PENDIENTE", "EN_PAUSA", "CERRADO", "ARCHIVADO", "REVISION"}
ALLOWED_CONFIDENCE = {"ALTA", "MEDIA", "BAJA"}


@dataclass(frozen=True)
class ProviderResult:
    payload: SemanticAnalysisPayload
    provider: str
    model: str
    response_id: str | None = None


class SemanticProvider(Protocol):
    def analyze(self, prompt_payload: dict) -> ProviderResult: ...


class DemoSemanticProvider:
    """Replays the approved O.T. 006 expected result and is never presented as a live model call."""

    def __init__(self, canonical_dir: Path, model: str) -> None:
        self.canonical_dir = canonical_dir
        self.model = model

    def analyze(self, prompt_payload: dict) -> ProviderResult:
        projects_data = self._load("expected_projects.json")["projects"]
        proposals_data = self._load("expected_proposals.json")["proposal_items"]
        evidence_data = {item["id"]: item for item in self._load("evidence.json")["evidence"]}
        chat_messages = {
            chat["id"]: chat.get("messages", []) for chat in prompt_payload["chats"]
        }

        projects: list[SemanticProjectPayload] = []
        for item in projects_data:
            memberships = [
                SemanticMembershipPayload(
                    chat_id=chat_id,
                    status="CONFIRMADA",
                    confidence="ALTA",
                    rationale="Asignación canónica aprobada en O.T. 006.",
                )
                for chat_id in item["chat_ids"]
            ]
            memberships.extend(
                SemanticMembershipPayload(
                    chat_id=chat_id,
                    status="DUDOSA",
                    confidence="MEDIA" if chat_id == "CHAT-014" else "BAJA",
                    rationale="La conversación comparte contexto con más de un proyecto.",
                )
                for chat_id in item.get("doubtful_chat_ids", [])
            )
            evidences: list[SemanticEvidencePayload] = []
            for evidence_id in item.get("evidence_ids", []):
                evidence = evidence_data[evidence_id]
                for chat_id in evidence["chat_ids"]:
                    message_id = self._match_message_id(chat_messages.get(chat_id, []), evidence["quote"])
                    evidences.append(
                        SemanticEvidencePayload(
                            chat_id=chat_id,
                            message_id=message_id,
                            kind=evidence["kind"],
                            quote=evidence["quote"],
                            precedence=evidence["precedence"],
                        )
                    )
            projects.append(
                SemanticProjectPayload(
                    project_key=item["id"],
                    name=item["name"],
                    description=self._description(item),
                    state=item["state"],
                    confidence="ALTA",
                    current_version=item.get("current_version"),
                    previous_versions=item.get("previous_versions", []),
                    discarded_versions=item.get("discarded_versions", []),
                    phase=item.get("phase"),
                    approved_decisions=item.get("approved_decisions", []),
                    superseded_decisions=[],
                    discarded_items=item.get("discarded_decisions", []),
                    pending_tasks=item.get("pending_tasks", []),
                    blockers=item.get("blockers", []),
                    last_confirmed_advance=item.get("last_confirmed_advance"),
                    next_probable_step=item.get("next_probable_step"),
                    memberships=memberships,
                    evidences=evidences,
                )
            )

        exceptions: list[SemanticExceptionPayload] = []
        for proposal in proposals_data:
            if not proposal.get("review_required"):
                continue
            target_ids = proposal.get("target_ids", [])
            exceptions.append(
                SemanticExceptionPayload(
                    chat_id=target_ids[0] if target_ids else None,
                    kind=proposal["operation"],
                    confidence=proposal["confidence"],
                    candidate_project_keys=proposal.get("candidate_project_ids", []),
                    reason=proposal["reason"],
                )
            )

        return ProviderResult(
            payload=SemanticAnalysisPayload(
                projects=projects,
                exceptions=exceptions,
                independent_chat_ids=["CHAT-026", "CHAT-027", "CHAT-028", "CHAT-030"],
                unclassified_chat_ids=["CHAT-029"],
            ),
            provider="APPROVED_DEMO_FIXTURE",
            model=self.model,
            response_id=None,
        )

    def _load(self, name: str) -> dict:
        return json.loads((self.canonical_dir / name).read_text(encoding="utf-8"))

    @staticmethod
    def _match_message_id(messages: list[dict], quote: str) -> str | None:
        normalized_quote = quote.casefold().rstrip(".")
        for message in messages:
            content = str(message.get("content", "")).casefold()
            if normalized_quote in content or content.rstrip(".") in normalized_quote:
                return message.get("id")
        return None

    @staticmethod
    def _description(item: dict) -> str:
        phase = item.get("phase") or "sin fase activa"
        return f"{item['name']}. Estado {item['state']}; fase: {phase}."


class OpenAISemanticProvider:
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for LIVE semantic analysis")
        self.settings = settings

    def analyze(self, prompt_payload: dict) -> ProviderResult:
        from openai import OpenAI

        client = OpenAI(api_key=self.settings.openai_api_key)
        response = client.responses.parse(
            model=self.settings.openai_model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(prompt_payload, ensure_ascii=False, sort_keys=True),
                },
            ],
            text_format=SemanticAnalysisPayload,
            reasoning={"effort": self.settings.openai_reasoning_effort},
            max_output_tokens=self.settings.openai_max_output_tokens,
            store=False,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError("OpenAI response did not contain structured semantic output")
        return ProviderResult(
            payload=parsed,
            provider="OPENAI_RESPONSES_API",
            model=self.settings.openai_model,
            response_id=response.id,
        )


SYSTEM_PROMPT = """You are the semantic project reconstruction engine for ChatGPT Project Organizer.
Analyze only the supplied normalized conversations and deterministic findings.
Return project grouping, operational memory, independent chats, unclassified chats, and exceptions.
Never propose or apply destructive operations. Original chats are immutable.
Evidence priority: latest explicit decision, explicit approval, validated version, confirmed test, explicit pending task, chronology, semantic inference, title metadata.
Use only external chat and message IDs supplied in the input. Do not invent IDs.
Exact duplicate copies must not be assigned as separate project memberships when a canonical chat is identified.
A working project with an approved future phase or pending task is ACTIVO, not CERRADO.
Use only ALTA, MEDIA, or BAJA confidence. Use REVISION only when evidence cannot resolve the lifecycle state.
Keep independent one-off conversations outside projects. Put insufficient or cross-project cases in exceptions.
The output must strictly match the supplied schema."""


class SemanticService:
    def __init__(self, engine: Engine, settings: Settings, provider: SemanticProvider | None = None) -> None:
        self.engine = engine
        self.settings = settings
        self.provider_override = provider

    def capabilities(self) -> SemanticCapabilityResponse:
        return SemanticCapabilityResponse(
            demo_available=True,
            live_available=bool(self.settings.openai_api_key),
            default_model=self.settings.openai_model,
            responses_api=True,
            structured_outputs=True,
        )

    def run(self, analysis_run_id: str, mode: str) -> SemanticRunResponse:
        normalized_mode = mode.upper()
        if normalized_mode not in {"DEMO", "LIVE"}:
            raise ValueError("mode must be DEMO or LIVE")
        with Session(self.engine) as session:
            analysis_run = session.scalar(
                select(AnalysisRun)
                .where(AnalysisRun.id == analysis_run_id)
                .options(
                    selectinload(AnalysisRun.findings).selectinload(AnalysisFinding.evidences),
                    selectinload(AnalysisRun.findings).selectinload(AnalysisFinding.chat),
                    selectinload(AnalysisRun.findings).selectinload(AnalysisFinding.related_chat),
                )
            )
            if analysis_run is None:
                raise KeyError(analysis_run_id)
            if analysis_run.status != "COMPLETED":
                raise ValueError("Deterministic analysis must be completed first")
            chats = list(
                session.scalars(
                    select(Chat)
                    .where(Chat.batch_id == analysis_run.batch_id)
                    .order_by(Chat.created_at, Chat.external_id)
                    .options(selectinload(Chat.messages))
                ).all()
            )
            prompt_payload = self._build_prompt_payload(analysis_run, chats)

        input_digest = hashlib.sha256(
            json.dumps(prompt_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        provider = self.provider_override or self._provider(normalized_mode)
        result = provider.analyze(prompt_payload)
        self._validate_payload(result.payload, chats, analysis_run)

        with Session(self.engine) as session:
            analysis_run = session.get(AnalysisRun, analysis_run_id)
            assert analysis_run is not None
            chat_by_external = {
                chat.external_id: chat
                for chat in session.scalars(
                    select(Chat)
                    .where(Chat.batch_id == analysis_run.batch_id)
                    .options(selectinload(Chat.messages))
                ).all()
            }
            run = SemanticRun(
                analysis_run_id=analysis_run_id,
                mode=normalized_mode,
                model=result.model,
                provider=result.provider,
                status="COMPLETED",
                completed_at=datetime.now(timezone.utc),
                input_digest=input_digest,
                openai_response_id=result.response_id,
                project_count=len(result.payload.projects),
                membership_count=sum(len(project.memberships) for project in result.payload.projects),
                exception_count=len(result.payload.exceptions),
                independent_chat_count=len(result.payload.independent_chat_ids),
                unclassified_chat_count=len(result.payload.unclassified_chat_ids),
                independent_chat_ids_json=json.dumps(result.payload.independent_chat_ids, ensure_ascii=False),
                unclassified_chat_ids_json=json.dumps(result.payload.unclassified_chat_ids, ensure_ascii=False),
                originals_modified=False,
            )
            session.add(run)
            session.flush()
            for project_payload in result.payload.projects:
                project = Project(
                    semantic_run_id=run.id,
                    project_key=project_payload.project_key,
                    name=project_payload.name,
                    description=project_payload.description,
                    state=project_payload.state,
                    confidence=project_payload.confidence,
                    current_version=project_payload.current_version,
                    previous_versions_json=json.dumps(project_payload.previous_versions, ensure_ascii=False),
                    discarded_versions_json=json.dumps(project_payload.discarded_versions, ensure_ascii=False),
                    phase=project_payload.phase,
                    approved_decisions_json=json.dumps(project_payload.approved_decisions, ensure_ascii=False),
                    superseded_decisions_json=json.dumps(project_payload.superseded_decisions, ensure_ascii=False),
                    discarded_items_json=json.dumps(project_payload.discarded_items, ensure_ascii=False),
                    pending_tasks_json=json.dumps(project_payload.pending_tasks, ensure_ascii=False),
                    blockers_json=json.dumps(project_payload.blockers, ensure_ascii=False),
                    last_confirmed_advance=project_payload.last_confirmed_advance,
                    next_probable_step=project_payload.next_probable_step,
                )
                session.add(project)
                session.flush()
                for membership_payload in project_payload.memberships:
                    chat = chat_by_external[membership_payload.chat_id]
                    session.add(
                        ProjectMembership(
                            project_id=project.id,
                            chat_id=chat.id,
                            status=membership_payload.status,
                            confidence=membership_payload.confidence,
                            rationale=membership_payload.rationale,
                        )
                    )
                for evidence_payload in project_payload.evidences:
                    chat = chat_by_external[evidence_payload.chat_id]
                    message = next(
                        (
                            message
                            for message in chat.messages
                            if message.external_id == evidence_payload.message_id
                        ),
                        None,
                    )
                    session.add(
                        ProjectEvidence(
                            project_id=project.id,
                            chat_id=chat.id,
                            message_id=message.id if message else None,
                            kind=evidence_payload.kind,
                            quote=evidence_payload.quote,
                            precedence=evidence_payload.precedence,
                        )
                    )
            for exception_payload in result.payload.exceptions:
                chat = chat_by_external.get(exception_payload.chat_id) if exception_payload.chat_id else None
                session.add(
                    SemanticException(
                        semantic_run_id=run.id,
                        chat_id=chat.id if chat else None,
                        kind=exception_payload.kind,
                        confidence=exception_payload.confidence,
                        candidate_project_keys_json=json.dumps(
                            exception_payload.candidate_project_keys, ensure_ascii=False
                        ),
                        reason=exception_payload.reason,
                    )
                )
            session.commit()
            run_id = run.id
        return self.get_run(run_id)

    def _provider(self, mode: str) -> SemanticProvider:
        if mode == "DEMO":
            return DemoSemanticProvider(self.settings.demo_data_dir, self.settings.openai_model)
        return OpenAISemanticProvider(self.settings)

    def _build_prompt_payload(self, analysis_run: AnalysisRun, chats: list[Chat]) -> dict:
        return {
            "contract": {
                "semantic_engine": SEMANTIC_ENGINE_VERSION,
                "originals_immutable": True,
                "allowed_states": sorted(ALLOWED_STATES),
                "allowed_confidence": ["ALTA", "MEDIA", "BAJA"],
            },
            "chats": [
                {
                    "id": chat.external_id,
                    "title": chat.title,
                    "created_at": chat.created_at.isoformat() if chat.created_at else None,
                    "updated_at": chat.updated_at.isoformat() if chat.updated_at else None,
                    "messages": [
                        {
                            "id": message.external_id,
                            "role": message.role,
                            "timestamp": message.timestamp.isoformat() if message.timestamp else None,
                            "content": message.content,
                        }
                        for message in chat.messages
                    ],
                }
                for chat in chats
            ],
            "deterministic_findings": [
                {
                    "type": finding.finding_type,
                    "subject": finding.subject,
                    "classification": finding.classification,
                    "confidence": finding.confidence,
                    "chat_id": finding.chat.external_id if finding.chat else None,
                    "related_chat_id": finding.related_chat.external_id if finding.related_chat else None,
                    "details": json.loads(finding.details_json),
                    "evidence": [
                        {
                            "chat_id": evidence.chat.external_id,
                            "message_id": evidence.message.external_id if evidence.message else None,
                            "kind": evidence.kind,
                            "quote": evidence.quote,
                            "precedence": evidence.precedence,
                        }
                        for evidence in finding.evidences
                    ],
                }
                for finding in analysis_run.findings
            ],
        }

    def _validate_payload(
        self, payload: SemanticAnalysisPayload, chats: list[Chat], analysis_run: AnalysisRun
    ) -> None:
        chat_ids = {chat.external_id for chat in chats}
        message_ids = {
            message.external_id
            for chat in chats
            for message in chat.messages
            if message.external_id is not None
        }
        project_keys = [project.project_key for project in payload.projects]
        if len(project_keys) != len(set(project_keys)):
            raise ValueError("Semantic output contains duplicate project keys")
        confirmed_memberships: dict[str, str] = {}
        exact_duplicates = {
            finding.chat.external_id
            for finding in analysis_run.findings
            if finding.finding_type == "EXACT_DUPLICATE" and finding.chat is not None
        }
        for project in payload.projects:
            if project.state not in ALLOWED_STATES or project.confidence not in ALLOWED_CONFIDENCE:
                raise ValueError("Semantic output contains an invalid state or confidence")
            for membership in project.memberships:
                if membership.chat_id not in chat_ids:
                    raise ValueError(f"Unknown membership chat id: {membership.chat_id}")
                if membership.chat_id in exact_duplicates:
                    raise ValueError("Exact duplicate copies cannot be assigned as separate memberships")
                if membership.status == "CONFIRMADA":
                    previous = confirmed_memberships.get(membership.chat_id)
                    if previous and previous != project.project_key:
                        raise ValueError("A chat cannot have two confirmed project memberships")
                    confirmed_memberships[membership.chat_id] = project.project_key
            for evidence in project.evidences:
                if evidence.chat_id not in chat_ids:
                    raise ValueError(f"Unknown evidence chat id: {evidence.chat_id}")
                if evidence.message_id is not None and evidence.message_id not in message_ids:
                    raise ValueError(f"Unknown evidence message id: {evidence.message_id}")
        known_project_keys = set(project_keys)
        for exception in payload.exceptions:
            if exception.chat_id is not None and exception.chat_id not in chat_ids:
                raise ValueError(f"Unknown exception chat id: {exception.chat_id}")
            if not set(exception.candidate_project_keys).issubset(known_project_keys):
                raise ValueError("Exception references an unknown project key")
        independent = set(payload.independent_chat_ids)
        unclassified = set(payload.unclassified_chat_ids)
        if not independent.issubset(chat_ids) or not unclassified.issubset(chat_ids):
            raise ValueError("Independent or unclassified output references an unknown chat")
        if independent & unclassified:
            raise ValueError("A chat cannot be both independent and unclassified")

    def list_runs(self) -> list[SemanticRunSummaryResponse]:
        with Session(self.engine) as session:
            runs = list(session.scalars(select(SemanticRun).order_by(SemanticRun.created_at.desc())).all())
            return [self._summary(run) for run in runs]

    def get_run(self, run_id: str) -> SemanticRunResponse:
        with Session(self.engine) as session:
            run = session.scalar(
                select(SemanticRun)
                .where(SemanticRun.id == run_id)
                .options(
                    selectinload(SemanticRun.projects)
                    .selectinload(Project.memberships)
                    .selectinload(ProjectMembership.chat),
                    selectinload(SemanticRun.projects)
                    .selectinload(Project.evidences)
                    .selectinload(ProjectEvidence.chat),
                    selectinload(SemanticRun.projects)
                    .selectinload(Project.evidences)
                    .selectinload(ProjectEvidence.message),
                    selectinload(SemanticRun.exceptions).selectinload(SemanticException.chat),
                )
            )
            if run is None:
                raise KeyError(run_id)
            projects = [self._project(project) for project in sorted(run.projects, key=lambda p: p.name)]
            exceptions = [self._exception(item) for item in run.exceptions]
            summary = self._summary(run)
            return SemanticRunResponse(
                **summary.model_dump(),
                projects=projects,
                exceptions=exceptions,
                independent_chat_ids=json.loads(run.independent_chat_ids_json),
                unclassified_chat_ids=json.loads(run.unclassified_chat_ids_json),
            )

    @staticmethod
    def _summary(run: SemanticRun) -> SemanticRunSummaryResponse:
        return SemanticRunSummaryResponse(
            id=run.id,
            analysis_run_id=run.analysis_run_id,
            mode=run.mode,
            model=run.model,
            provider=run.provider,
            status=run.status,
            created_at=run.created_at,
            completed_at=run.completed_at,
            input_digest=run.input_digest,
            openai_response_id=run.openai_response_id,
            project_count=run.project_count,
            membership_count=run.membership_count,
            exception_count=run.exception_count,
            independent_chat_count=run.independent_chat_count,
            unclassified_chat_count=run.unclassified_chat_count,
            originals_modified=run.originals_modified,
        )

    @staticmethod
    def _project(project: Project) -> ProjectResponse:
        return ProjectResponse(
            id=project.id,
            project_key=project.project_key,
            name=project.name,
            description=project.description,
            state=project.state,
            confidence=project.confidence,
            current_version=project.current_version,
            previous_versions=json.loads(project.previous_versions_json),
            discarded_versions=json.loads(project.discarded_versions_json),
            phase=project.phase,
            approved_decisions=json.loads(project.approved_decisions_json),
            superseded_decisions=json.loads(project.superseded_decisions_json),
            discarded_items=json.loads(project.discarded_items_json),
            pending_tasks=json.loads(project.pending_tasks_json),
            blockers=json.loads(project.blockers_json),
            last_confirmed_advance=project.last_confirmed_advance,
            next_probable_step=project.next_probable_step,
            memberships=[
                ProjectMembershipResponse(
                    id=membership.id,
                    chat_external_id=membership.chat.external_id,
                    chat_title=membership.chat.title,
                    status=membership.status,
                    confidence=membership.confidence,
                    rationale=membership.rationale,
                )
                for membership in sorted(project.memberships, key=lambda m: m.chat.external_id)
            ],
            evidences=[
                ProjectEvidenceResponse(
                    id=evidence.id,
                    chat_external_id=evidence.chat.external_id,
                    message_external_id=evidence.message.external_id if evidence.message else None,
                    kind=evidence.kind,
                    quote=evidence.quote,
                    precedence=evidence.precedence,
                )
                for evidence in sorted(project.evidences, key=lambda e: (e.precedence, e.chat.external_id))
            ],
        )

    @staticmethod
    def _exception(item: SemanticException) -> SemanticExceptionResponse:
        return SemanticExceptionResponse(
            id=item.id,
            chat_external_id=item.chat.external_id if item.chat else None,
            chat_title=item.chat.title if item.chat else None,
            kind=item.kind,
            confidence=item.confidence,
            candidate_project_keys=json.loads(item.candidate_project_keys_json),
            reason=item.reason,
        )

"""Framework-light Phase 3 publication governance contracts.

The committed JSONL file is a read-only validation input.  It is deliberately not a
mutable production decision store.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Protocol, Sequence


class PublicationClass(StrEnum):
    LEGACY_COMPATIBILITY = "LEGACY_COMPATIBILITY"
    GOVERNED_RECORD = "GOVERNED_RECORD"


class EditorialState(StrEnum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    READY_FOR_INSTITUTIONAL_REVIEW = "READY_FOR_INSTITUTIONAL_REVIEW"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"


class InstitutionalDecision(StrEnum):
    NOT_SUBMITTED = "NOT_SUBMITTED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class EligibilityOutcome(StrEnum):
    LEGACY_VISIBLE = "LEGACY_VISIBLE"
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    REVOKED = "REVOKED"
    CONFIGURATION_BLOCKED = "CONFIGURATION_BLOCKED"


@dataclass(frozen=True, slots=True)
class EffectiveDecision:
    state: InstitutionalDecision
    canonical_content_hash: str
    ambiguous: bool = False
    expires_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class EligibilityRequest:
    publication_class: PublicationClass
    canonical_content_hash: str
    editorial_state: EditorialState
    technically_valid: bool
    runtime_published: bool
    runtime_active: bool
    legacy_baseline_match: bool = False


@dataclass(frozen=True, slots=True)
class EligibilityResult:
    outcome: EligibilityOutcome
    institutionally_approved: bool
    code: str


class DecisionSource(Protocol):
    def effective_decision(self, subject_type: str, subject_id: str) -> EffectiveDecision | None: ...
    def history(self, subject_type: str, subject_id: str) -> Sequence["ApprovalEvent"]: ...
    def append(self, event: "ApprovalEvent") -> None: ...


def evaluate_eligibility(request: EligibilityRequest, decision: EffectiveDecision | None) -> EligibilityResult:
    if not request.runtime_published or not request.runtime_active:
        return EligibilityResult(EligibilityOutcome.INELIGIBLE, False, "PUBLICATION_RUNTIME_INACTIVE")
    if request.publication_class is PublicationClass.LEGACY_COMPATIBILITY:
        if request.legacy_baseline_match:
            return EligibilityResult(EligibilityOutcome.LEGACY_VISIBLE, False, "PUBLICATION_LEGACY_COMPATIBILITY")
        return EligibilityResult(EligibilityOutcome.INELIGIBLE, False, "PUBLICATION_LEGACY_MISMATCH")
    if decision is None:
        return EligibilityResult(EligibilityOutcome.INELIGIBLE, False, "PUBLICATION_DECISION_MISSING")
    if decision.ambiguous:
        return EligibilityResult(EligibilityOutcome.CONFIGURATION_BLOCKED, False, "PUBLICATION_DECISION_AMBIGUOUS")
    if decision.state is InstitutionalDecision.REVOKED:
        return EligibilityResult(EligibilityOutcome.REVOKED, False, "PUBLICATION_DECISION_REVOKED")
    if decision.state is InstitutionalDecision.EXPIRED or (
        decision.expires_at is not None and decision.expires_at <= datetime.now(UTC)
    ):
        return EligibilityResult(EligibilityOutcome.INELIGIBLE, False, "PUBLICATION_DECISION_EXPIRED")
    gates = (
        request.editorial_state is EditorialState.READY_FOR_INSTITUTIONAL_REVIEW,
        request.technically_valid,
        decision.state is InstitutionalDecision.APPROVED,
        decision.canonical_content_hash == request.canonical_content_hash,
    )
    if all(gates):
        return EligibilityResult(EligibilityOutcome.ELIGIBLE, True, "PUBLICATION_ELIGIBLE")
    return EligibilityResult(EligibilityOutcome.INELIGIBLE, False, "PUBLICATION_GATES_INCOMPLETE")


@dataclass(frozen=True, slots=True)
class ApprovalEvent:
    schema_version: int
    event_id: str
    subject_type: str
    subject_id: str
    action: str
    previous_state: InstitutionalDecision
    resulting_state: InstitutionalDecision
    canonical_content_hash: str
    actor_id: str
    institutional_role: str
    evidence_reference: str
    reason: str
    timestamp: datetime
    superseded_event_id: str | None = None
    submitter_actor_id: str | None = None


ALLOWED_TRANSITIONS = {
    (InstitutionalDecision.NOT_SUBMITTED, InstitutionalDecision.PENDING),
    (InstitutionalDecision.PENDING, InstitutionalDecision.APPROVED),
    (InstitutionalDecision.PENDING, InstitutionalDecision.REJECTED),
    (InstitutionalDecision.REJECTED, InstitutionalDecision.PENDING),
    (InstitutionalDecision.APPROVED, InstitutionalDecision.REVOKED),
    (InstitutionalDecision.APPROVED, InstitutionalDecision.EXPIRED),
}


class TransitionError(ValueError): pass


def validate_transition(event: ApprovalEvent, existing: Sequence[ApprovalEvent]) -> None:
    required = (event.event_id, event.subject_type, event.subject_id, event.action,
                event.canonical_content_hash, event.actor_id, event.institutional_role,
                event.evidence_reference, event.reason)
    if event.schema_version != 1 or any(not value.strip() for value in required):
        raise TransitionError("PUBLICATION_TRANSITION_REQUIRED_FIELD_MISSING")
    if len(event.canonical_content_hash) != 64 or any(c not in "0123456789abcdef" for c in event.canonical_content_hash):
        raise TransitionError("PUBLICATION_CONTENT_HASH_INVALID")
    if any(item.event_id == event.event_id for item in existing):
        raise TransitionError("PUBLICATION_EVENT_ID_DUPLICATE")
    if (event.previous_state, event.resulting_state) not in ALLOWED_TRANSITIONS:
        raise TransitionError("PUBLICATION_TRANSITION_INVALID")
    subject_history = [item for item in existing if item.subject_type == event.subject_type and item.subject_id == event.subject_id]
    effective = subject_history[-1].resulting_state if subject_history else InstitutionalDecision.NOT_SUBMITTED
    if effective is not event.previous_state:
        raise TransitionError("PUBLICATION_PREVIOUS_STATE_MISMATCH")
    if event.resulting_state is InstitutionalDecision.APPROVED:
        if event.institutional_role != "publication_approver":
            raise TransitionError("PUBLICATION_ROLE_NOT_AUTHORIZED")
        if event.submitter_actor_id == event.actor_id:
            raise TransitionError("PUBLICATION_SELF_APPROVAL_PROHIBITED")


class InMemoryDecisionSource:
    """Single-process test adapter; never production storage."""
    def __init__(self) -> None: self._events: list[ApprovalEvent] = []
    def history(self, subject_type: str, subject_id: str) -> tuple[ApprovalEvent, ...]:
        return tuple(e for e in self._events if e.subject_type == subject_type and e.subject_id == subject_id)
    def append(self, event: ApprovalEvent) -> None:
        validate_transition(event, self._events)
        self._events.append(event)
    def effective_decision(self, subject_type: str, subject_id: str) -> EffectiveDecision | None:
        history = self.history(subject_type, subject_id)
        if not history: return None
        last = history[-1]
        return EffectiveDecision(last.resulting_state, last.canonical_content_hash)


class ReadOnlyRepositoryLedger:
    def __init__(self, path: Path) -> None: self.path = path
    def history(self, subject_type: str, subject_id: str) -> tuple[ApprovalEvent, ...]:
        events: list[ApprovalEvent] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip(): continue
            raw = json.loads(line)
            if raw.get("subject_type") == subject_type and str(raw.get("subject_id")) == subject_id:
                raw["previous_state"] = InstitutionalDecision(raw["previous_state"])
                raw["resulting_state"] = InstitutionalDecision(raw["resulting_state"])
                raw["timestamp"] = datetime.fromisoformat(raw["timestamp"].replace("Z", "+00:00"))
                events.append(ApprovalEvent(**raw))
        return tuple(events)
    def effective_decision(self, subject_type: str, subject_id: str) -> EffectiveDecision | None:
        history = self.history(subject_type, subject_id)
        if not history: return None
        last = history[-1]
        return EffectiveDecision(last.resulting_state, last.canonical_content_hash)
    def append(self, event: ApprovalEvent) -> None:
        raise TransitionError("PUBLICATION_REPOSITORY_LEDGER_READ_ONLY")


def canonical_hash(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class LegacyDestinationCatalog:
    """Exact fingerprints derived from the frozen development seed artifact."""
    def __init__(self, dataset_path: Path) -> None:
        payload = json.loads(dataset_path.read_text(encoding="utf-8"))
        self._hashes = {
            item["slug"]: canonical_hash(self.normalize(item))
            for item in payload["records"]
        }

    @staticmethod
    def normalize(item: dict[str, object]) -> dict[str, object]:
        translations = []
        for value in item.get("translations", []):
            translation = dict(value)
            translations.append({
                key: translation.get(key)
                for key in ("language_code", "name", "short_description", "description",
                            "historical_background", "visitor_information",
                            "accessibility_information", "seo_title", "seo_description")
            })
        return {
            "slug": item.get("slug"), "category": item.get("category"),
            "status": item.get("status", "draft"), "is_active": item.get("is_active", True),
            "is_featured": item.get("is_featured", False),
            "priority_order": item.get("priority_order", 0),
            "municipality": item.get("municipality"), "region": item.get("region"),
            "latitude": item.get("latitude"), "longitude": item.get("longitude"),
            "translations": translations,
        }

    def matches(self, snapshot: dict[str, object]) -> bool:
        slug = str(snapshot.get("slug", ""))
        expected = self._hashes.get(slug)
        return expected is not None and expected == canonical_hash(self.normalize(snapshot))

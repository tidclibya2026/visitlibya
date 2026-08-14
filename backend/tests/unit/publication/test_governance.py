from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.publication.governance import (
    ApprovalEvent, EditorialState, EffectiveDecision, EligibilityOutcome,
    EligibilityRequest, InMemoryDecisionSource, InstitutionalDecision,
    LegacyDestinationCatalog, PublicationClass, ReadOnlyRepositoryLedger,
    TransitionError, evaluate_eligibility,
)

ROOT = Path(__file__).resolve().parents[4]
HASH = "a" * 64


def request(**values):
    defaults = dict(publication_class=PublicationClass.GOVERNED_RECORD,
                    canonical_content_hash=HASH,
                    editorial_state=EditorialState.READY_FOR_INSTITUTIONAL_REVIEW,
                    technically_valid=True, runtime_published=True, runtime_active=True)
    defaults.update(values)
    return EligibilityRequest(**defaults)


def event(event_id="event-1", previous=InstitutionalDecision.NOT_SUBMITTED,
          resulting=InstitutionalDecision.PENDING, actor="actor-submit",
          role="data_preparer", submitter=None):
    return ApprovalEvent(1, event_id, "destination", "synthetic-1", "TRANSITION",
                         previous, resulting, HASH, actor, role, "evidence:test-only",
                         "synthetic test reason", datetime.now(UTC),
                         submitter_actor_id=submitter)


def test_legacy_baseline_visible_but_never_approved():
    result = evaluate_eligibility(request(publication_class=PublicationClass.LEGACY_COMPATIBILITY,
                                          legacy_baseline_match=True), None)
    assert result.outcome is EligibilityOutcome.LEGACY_VISIBLE
    assert result.institutionally_approved is False


@pytest.mark.parametrize("change", [
    {"runtime_published": False}, {"runtime_active": False},
    {"editorial_state": EditorialState.DRAFT}, {"technically_valid": False},
])
def test_individual_runtime_editorial_or_technical_gate_is_insufficient(change):
    assert evaluate_eligibility(request(**change), None).outcome is EligibilityOutcome.INELIGIBLE


def test_published_active_governed_record_without_decision_fails_closed():
    assert evaluate_eligibility(request(), None).code == "PUBLICATION_DECISION_MISSING"


def test_isolated_approved_decision_with_all_gates_is_eligible():
    result = evaluate_eligibility(request(), EffectiveDecision(InstitutionalDecision.APPROVED, HASH))
    assert result.outcome is EligibilityOutcome.ELIGIBLE and result.institutionally_approved


@pytest.mark.parametrize("state,outcome", [
    (InstitutionalDecision.REJECTED, EligibilityOutcome.INELIGIBLE),
    (InstitutionalDecision.REVOKED, EligibilityOutcome.REVOKED),
    (InstitutionalDecision.EXPIRED, EligibilityOutcome.INELIGIBLE),
])
def test_adverse_decisions_are_ineligible(state, outcome):
    assert evaluate_eligibility(request(), EffectiveDecision(state, HASH)).outcome is outcome


def test_expiry_hash_mismatch_and_ambiguity_fail_closed():
    expired = EffectiveDecision(InstitutionalDecision.APPROVED, HASH, expires_at=datetime.now(UTC)-timedelta(seconds=1))
    assert evaluate_eligibility(request(), expired).outcome is EligibilityOutcome.INELIGIBLE
    assert evaluate_eligibility(request(), EffectiveDecision(InstitutionalDecision.APPROVED, "b"*64)).outcome is EligibilityOutcome.INELIGIBLE
    assert evaluate_eligibility(request(), EffectiveDecision(InstitutionalDecision.APPROVED, HASH, ambiguous=True)).outcome is EligibilityOutcome.CONFIGURATION_BLOCKED


def test_legacy_mismatch_cannot_extend_compatibility():
    result = evaluate_eligibility(request(publication_class=PublicationClass.LEGACY_COMPATIBILITY,
                                          legacy_baseline_match=False), None)
    assert result.code == "PUBLICATION_LEGACY_MISMATCH"


def test_frozen_catalog_matches_only_exact_seed_contract():
    import json
    path = ROOT / "backend/data/dev/destinations.json"
    payload = json.loads(path.read_text(encoding="utf-8"))["records"][0]
    catalog = LegacyDestinationCatalog(path)
    assert catalog.matches(payload)
    changed = dict(payload, region="changed")
    assert not catalog.matches(changed)


def test_transition_history_append_only_unique_and_previous_state_enforced():
    source = InMemoryDecisionSource()
    first = event()
    source.append(first)
    assert source.history("destination", "synthetic-1") == (first,)
    with pytest.raises(TransitionError, match="DUPLICATE"): source.append(first)
    with pytest.raises(TransitionError, match="PREVIOUS_STATE"): source.append(event("event-2"))


def test_invalid_transition_unknown_role_missing_identity_evidence_and_self_approval_fail():
    source = InMemoryDecisionSource(); source.append(event())
    with pytest.raises(TransitionError, match="TRANSITION_INVALID"):
        source.append(event("bad", InstitutionalDecision.PENDING, InstitutionalDecision.REVOKED))
    with pytest.raises(TransitionError, match="REQUIRED_FIELD"):
        source.append(event("missing-actor", InstitutionalDecision.PENDING,
                            InstitutionalDecision.APPROVED, actor="", role="publication_approver"))
    with pytest.raises(TransitionError, match="REQUIRED_FIELD"):
        source.append(ApprovalEvent(1, "missing-evidence", "destination", "synthetic-1", "APPROVE",
                                    InstitutionalDecision.PENDING, InstitutionalDecision.APPROVED,
                                    HASH, "actor-a", "publication_approver", "", "reason", datetime.now(UTC)))
    with pytest.raises(TransitionError, match="ROLE_NOT_AUTHORIZED"):
        source.append(event("admin", InstitutionalDecision.PENDING,
                            InstitutionalDecision.APPROVED, role="admin"))
    with pytest.raises(TransitionError, match="ROLE_NOT_AUTHORIZED"):
        source.append(event("content-admin", InstitutionalDecision.PENDING,
                            InstitutionalDecision.APPROVED, role="content_admin"))
    with pytest.raises(TransitionError, match="SELF_APPROVAL"):
        source.append(event("self", InstitutionalDecision.PENDING,
                            InstitutionalDecision.APPROVED, actor="same", role="publication_approver", submitter="same"))


def test_repository_ledger_is_empty_and_read_only():
    path = ROOT / "backend/data/governance/publication-approval-ledger.jsonl"
    assert path.read_bytes() == b""
    source = ReadOnlyRepositoryLedger(path)
    assert source.effective_decision("destination", "x") is None
    with pytest.raises(TransitionError, match="READ_ONLY"): source.append(event())

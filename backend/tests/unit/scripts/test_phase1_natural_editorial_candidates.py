from __future__ import annotations
import copy,json,re
from collections import Counter
import pytest
from scripts.phase1_natural_editorial_candidates import ARTIFACT_PATH,CATEGORIES,EXPECTED_GLOBAL,EXPECTED_PRIORITY,EXPECTED_QUEUES,EXPECTED_RESOLUTION,FALSE_FIELDS,GOVERNED_SHA256,MANDATORY_NAMES,Phase1EditorialError,expected_editorial_id,validate_artifact,validate_serialization

@pytest.fixture
def artifact():return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
def candidates(a):return [x for c in CATEGORIES for x in a["candidate_queues"][c]]

def test_valid_artifact_passes(artifact):
    assert validate_artifact(artifact,check_git=False)=={"governed_ordinals":945,"evaluated":676,"eligible_candidates":383,"excluded_or_deferred":562,"queues":EXPECTED_QUEUES};validate_serialization()

def test_governed_and_external_provenance(artifact):
    p=artifact["source_provenance"];assert p["governed_input_sha256"]==GOVERNED_SHA256;assert p["governed_input_record_count"]==945;assert len(p["external_audit_inputs"])==5;assert p["absolute_source_path_recorded"] is False;assert p["ordinary_validation_requires_external_inputs"] is False

def test_exact_queue_counts(artifact):assert {c:len(artifact["candidate_queues"][c]) for c in CATEGORIES}==EXPECTED_QUEUES
def test_exact_priority_distribution(artifact):assert Counter(x["editorial_priority_band"] for x in candidates(artifact))==Counter({k:v for k,v in EXPECTED_PRIORITY.items() if v})
def test_global_accounting(artifact):assert all(artifact["global_accounting"][k]==v for k,v in EXPECTED_GLOBAL.items()) and sum(EXPECTED_RESOLUTION.values())==945

def test_ordinal_resolution_is_exact(artifact):
    rows=artifact["ordinal_resolution"];assert [x["source_ordinal"] for x in rows]==list(range(1,946));assert Counter(x["state"] for x in rows)==Counter(EXPECTED_RESOLUTION)

def test_candidate_ids_are_deterministic_unique(artifact):
    rows=candidates(artifact);assert len({x["editorial_review_id"] for x in rows})==383;assert all(x["editorial_review_id"]==expected_editorial_id(x) for x in rows)

def test_candidates_are_clean_new_and_nonoverlapping(artifact):
    for x in candidates(artifact):assert x["eligibility_state"]=="ELIGIBLE_NEW_EDITORIAL_CANDIDATE" and x["exclusion_reasons"]==[] and x["clean_governed_record"] is True and x["overlap_state"]=="NO_INSPECTED_GOVERNED_OVERLAP" and x["mandatory_display_exclusion"] is False

def test_candidate_source_evidence_is_complete(artifact):
    required={"raw_id","raw_name","proposed_normalized_name","raw_primary_category","raw_all_categories","raw_description","raw_folders","raw_source","raw_origin","raw_status","raw_source_type","preserved_properties","geometry","quality_flags","existing_governed_overlaps","source_geometry_metadata_mismatch","governed_resolution_bucket","governed_review_collection"}
    assert all(required==set(x["source_evidence"]) for x in candidates(artifact));assert all(len(x["source_evidence"]["preserved_properties"])>=12 for x in candidates(artifact))

def test_all_candidate_governance_is_unresolved(artifact):
    for x in candidates(artifact):assert all(x[f] is False for f in FALSE_FIELDS) and x["institutional_review_status"]=="UNRESOLVED" and x["canonical_destination"] is None

@pytest.mark.parametrize("field",FALSE_FIELDS)
def test_candidate_approval_fails_closed(artifact,field):
    invalid=copy.deepcopy(artifact);invalid["candidate_queues"]["NATURAL_SPRINGS"][0][field]=True
    with pytest.raises(Phase1EditorialError,match=field):validate_artifact(invalid,check_git=False)

def test_candidate_overlap_fails_closed(artifact):
    invalid=copy.deepcopy(artifact);invalid["candidate_queues"]["NATURAL_SPRINGS"][0]["overlap_state"]="DIRECT_CURATED_SOURCE_ID_OVERLAP"
    with pytest.raises(Phase1EditorialError,match="overlap queued"):validate_artifact(invalid,check_git=False)

def test_queue_count_drift_fails_closed(artifact):
    invalid=copy.deepcopy(artifact);invalid["candidate_queues"]["ISLANDS"].pop()
    with pytest.raises(Phase1EditorialError,match="queue counts|candidate count"):validate_artifact(invalid,check_git=False)

def test_same_name_and_near_candidates_are_not_consolidated(artifact):
    rows=candidates(artifact);assert sum(x["duplicate_conflict_state"]=="SAME_NAME_DIFFERENT_COORDINATE" for x in rows)==71;assert sum(x["duplicate_conflict_state"].startswith("NEAR_COORDINATE") for x in rows)==3

def test_missing_description_and_media_counts(artifact):
    rows=candidates(artifact);assert sum(x["description_quality"]=="MISSING" for x in rows)==367;assert sum(x["media_availability"]=="REPOSITORY_ASSET_AVAILABLE" for x in rows)==0;assert sum(x["media_rights_status"]!="NO_INDEPENDENT_RIGHTS_EVIDENCE" for x in rows)==0;assert all(x["publication_media_eligible"] is False for x in rows)

def test_all_dams_require_institutional_safety_review(artifact):
    dams=artifact["candidate_queues"]["DAMS_AND_RESERVOIRS_REVIEW"];required=set(artifact["institutional_review_policy"]["dam_requirements"]);assert len(dams)==23;assert artifact["institutional_review_policy"]["dams_are_infrastructure_associated_not_purely_natural"] is True;assert all(required<=set(x["required_human_review_actions"]) for x in dams)

def test_mountain_and_coast_gaps_remain_zero(artifact):
    assert artifact["candidate_queues"]["MOUNTAINS_AND_HIGHLANDS"]==[];assert artifact["candidate_queues"]["NATURAL_COASTS_AND_BEACHES"]==[];assert artifact["institutional_review_policy"]["mountain_source_gap"] is True;assert artifact["institutional_review_policy"]["new_coast_or_beach_candidate_gap"] is True

def test_mandatory_exclusions_remain_outside_queues(artifact):
    rows=candidates(artifact);assert not ({1,2,3,4}&{x["source_ordinal"] for x in rows});found={x["source_ordinal"]:x["source_evidence"]["raw_name"] for x in artifact["non_phase1_resolution_evidence"] if x["resolution_state"]=="MANDATORY_DISPLAY_EXCLUSION"};assert found==MANDATORY_NAMES

def test_exclusion_and_deferral_representation(artifact):
    assert len(artifact["evaluated_exclusions_and_deferrals"])==293;assert len(artifact["non_phase1_resolution_evidence"])==269;assert len(candidates(artifact))+len(artifact["evaluated_exclusions_and_deferrals"])+len(artifact["non_phase1_resolution_evidence"])==945

def test_score_arithmetic_and_range(artifact):
    keys=("identity_clarity","coordinate_quality","description_completeness","institutional_provenance","duplicate_conflict_safety","media_readiness_and_rights")
    for x in candidates(artifact):s=x["editorial_readiness_score"];assert s["total"]==sum(s[k] for k in keys);assert 0<=s["total"]<=100

def test_publication_and_registry_invariants(artifact):
    x=artifact["publication_and_protected_invariants"];assert (x["green_mountain_curated_features"],x["libyan_sahara_curated_features"],x["curated_frontend_total"],x["national_publication_gis_count"])==(180,69,249,214);assert x["approval_ledger_empty"] is True;assert x["registry_modified"] is False;assert x["source_manifest_modified"] is False;assert x["runtime_or_frontend_modified"] is False

def test_serialization_is_utf8_lf_and_portable():
    raw=ARTIFACT_PATH.read_bytes();assert not raw.startswith(b"\xef\xbb\xbf");assert b"\r\n" not in raw;assert raw.endswith(b"\n") and not raw.endswith(b"\n\n");assert b"visitlibya-local-backups" not in raw;assert not re.search(rb"[A-Za-z]:\\",raw)

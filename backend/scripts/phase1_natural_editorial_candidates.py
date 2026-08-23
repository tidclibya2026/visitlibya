#!/usr/bin/env python3
"""Build and validate the governed Phase 1 natural editorial candidate review."""
from __future__ import annotations
import hashlib,json,math,re,subprocess,sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
ARTIFACT_PATH=ROOT/"backend/data/gis/phase1-natural-editorial-candidates.review.json"
GOVERNED_PATH=ROOT/"backend/data/gis/national-natural-resources-source-reconciliation.review.json"
GOVERNED_RELATIVE="backend/data/gis/national-natural-resources-source-reconciliation.review.json"
GOVERNED_SHA256="501a23c24aeef24f84238a99d91a93de6f8a5b55e98763002f7da47cb617c8ac"
EXTERNAL_HASHES={
"phase1-natural-editorial-candidate-inventory.json":"2352b219892dc860b68b57856b7e4cc6f35834996f8d53c6005603160e539a0e",
"phase1-natural-editorial-readiness-audit.json":"cb15d67b0566fb307748a709e3a43c6d06db658ed750c26bbdb60b0b363f35ea",
"audit_phase1_natural_editorial_candidates.py":"a92a655540edac66ba6db0ee5b965b87ef367b38736a4fb1e628fc732d4500ad",
"validate_phase1_natural_editorial_audit.py":"0a26ccd45c57221db6f425f0e58f2fed17936e37addd97fb468d462244cf263e",
"phase1-natural-editorial-review-hashes.json":"e356f5f7c3d4615a94097a74c3a56143afa1051005a941c172460310729cc4a5",
}
CATEGORIES=("NATURAL_SPRINGS","DAMS_AND_RESERVOIRS_REVIEW","NATURAL_AND_DESERT_LAKES","CAVES_AND_ROCK_FORMATIONS","OASES_AND_PALM_LANDSCAPES","MOUNTAINS_AND_HIGHLANDS","NATURAL_COASTS_AND_BEACHES","ISLANDS","VALLEYS_AND_WADIS")
EXPECTED_QUEUES={"NATURAL_SPRINGS":91,"DAMS_AND_RESERVOIRS_REVIEW":23,"NATURAL_AND_DESERT_LAKES":9,"CAVES_AND_ROCK_FORMATIONS":3,"OASES_AND_PALM_LANDSCAPES":1,"MOUNTAINS_AND_HIGHLANDS":0,"NATURAL_COASTS_AND_BEACHES":0,"ISLANDS":2,"VALLEYS_AND_WADIS":254}
EXPECTED_PRIORITY={"HIGH_EDITORIAL_PRIORITY":7,"MEDIUM_EDITORIAL_PRIORITY":307,"LOW_EDITORIAL_PRIORITY":69,"DEFERRED":0}
EXPECTED_RESOLUTION={"ELIGIBLE_NEW_EDITORIAL_CANDIDATE":383,"EXISTING_GOVERNED_OVERLAP_EXCLUSION":224,"MANDATORY_DISPLAY_EXCLUSION":4,"NON_NATURAL_OR_MIXED_EXCLUSION":28,"OTHER_WATER_RESOURCE_DEFERRED":258,"OUTSIDE_PHASE1_NON_WATER_SCOPE":7,"SUBTYPE_IDENTITY_DEFERRAL":41}
EXPECTED_GLOBAL={"governed_source_records":945,"total_phase1_records_evaluated":676,"eligible_new_editorial_candidates":383,"excluded_existing_governed_overlaps":224,"excluded_non_natural_or_mixed_records":28,"mandatory_display_exclusions":4,"duplicate_conflict_deferrals":0,"subtype_identity_deferrals":41,"other_technical_deferrals":0,"deferred_water_records_outside_nine_categories":258,"outside_phase1_non_water_scope":7,"resolved_governed_ordinals":945}
FALSE_FIELDS=("publication_approved","canonical_approval","public_visibility_enabled","publication_media_eligible","editorial_selection_is_approval")
MANDATORY_NAMES={1:"أطلال حصن بئر احكيم",2:"الفرارة موقع أثري مغمور بالمياه",3:"المقبرة الايطالية",4:"المنطقة الجنائزية"}
ALLOWED_CHANGED={"backend/data/gis/phase1-natural-editorial-candidates.review.json","backend/scripts/phase1_natural_editorial_candidates.py","backend/tests/unit/scripts/test_phase1_natural_editorial_candidates.py","backend/docs/phase1-natural-editorial-candidates.md"}
PROTECTED=("backend/data/destinations/national-destination-registry.review.json","backend/scripts/destination_registry.py","backend/data/gis/source-manifest.json","backend/data/gis/institutional-sources.json","backend/data/gis/green-mountain-tourism-curated.review.json","backend/data/gis/libyan-sahara-tourism-curated.review.json","backend/data/governance","assets","backend/app","backend/models","backend/migrations")

class Phase1EditorialError(ValueError):pass
def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()
def canonical(value:Any)->bytes:return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")
def committed_governed_bytes(root:Path=ROOT)->bytes:
    raw=subprocess.check_output(["git","cat-file","blob",f"HEAD:{GOVERNED_RELATIVE}"],cwd=root)
    if sha(raw)!=GOVERNED_SHA256:raise Phase1EditorialError("committed governed input SHA-256 mismatch")
    return raw
def governed_records(governed:dict)->dict[int,dict]:return {r["source_ordinal"]:r for c in governed["collections"].values() for r in c}
def expected_editorial_id(record:dict)->str:
    return "nnr-phase1-"+sha(canonical({"governed_input_sha256":GOVERNED_SHA256,"source_ordinal":record.get("source_ordinal"),"governed_review_id":record.get("governed_review_id"),"priority_category":record.get("priority_category")}))[:24]
def source_evidence(source:dict)->dict:
    return {"raw_id":source["raw_id"],"raw_name":source["raw_name"],"proposed_normalized_name":source["proposed_normalized_name"],"raw_primary_category":source["raw_primary_category"],"raw_all_categories":source["raw_all_categories"],"raw_description":source["raw_description"],"raw_folders":source["raw_folders"],"raw_source":source["raw_source"],"raw_origin":source["raw_origin"],"raw_status":source["raw_status"],"raw_source_type":source["raw_source_type"],"preserved_properties":source["preserved_properties"],"geometry":source["geometry"],"quality_flags":source["quality_flags"],"existing_governed_overlaps":source["existing_governed_overlaps"],"source_geometry_metadata_mismatch":source["source_geometry_metadata_mismatch"],"governed_resolution_bucket":source["resolution_bucket"],"governed_review_collection":source["proposed_review_collection"]}

def build_artifact(audit_dir:Path,root:Path=ROOT)->dict:
    for name,digest in EXTERNAL_HASHES.items():
        p=audit_dir/name
        if not p.is_file() or sha(p.read_bytes())!=digest:raise Phase1EditorialError(f"external audit hash mismatch: {name}")
    governed=json.loads(committed_governed_bytes(root)); sources=governed_records(governed)
    inventory=json.loads((audit_dir/"phase1-natural-editorial-candidate-inventory.json").read_text(encoding="utf-8")); audit=json.loads((audit_dir/"phase1-natural-editorial-readiness-audit.json").read_text(encoding="utf-8"))
    if len(sources)!=945 or set(sources)!=set(range(1,946)):raise Phase1EditorialError("governed source accounting mismatch")
    queues={category:[] for category in CATEGORIES}; exclusions=[]
    for evaluation in inventory["evaluated_records"]:
        item=dict(evaluation);item["source_evidence"]=source_evidence(sources[item["source_ordinal"]])
        if item["eligibility_state"]=="ELIGIBLE_NEW_EDITORIAL_CANDIDATE":queues[item["priority_category"]].append(item)
        else:exclusions.append(item)
    queue_order={category:{entry["editorial_review_id"]:entry["queue_position"] for entry in audit["institutional_review_queues"][category]} for category in CATEGORIES}
    for category in CATEGORIES:queues[category].sort(key=lambda x:queue_order[category][x["editorial_review_id"]])
    exclusions.sort(key=lambda x:x["source_ordinal"])
    nonphase=[]
    for section,state in (("mandatory_display_exclusion_records","MANDATORY_DISPLAY_EXCLUSION"),("deferred_water_records","OTHER_WATER_RESOURCE_DEFERRED"),("outside_phase1_non_water_records","OUTSIDE_PHASE1_NON_WATER_SCOPE")):
        for evidence in inventory[section]:
            source=sources[evidence["source_ordinal"]]
            nonphase.append({**evidence,"resolution_state":state,"source_evidence":source_evidence(source),"publication_approved":False,"canonical_approval":False,"public_visibility_enabled":False,"publication_media_eligible":False,"institutional_review_status":"UNRESOLVED","canonical_destination":None,"editorial_selection_is_approval":False})
    nonphase.sort(key=lambda x:x["source_ordinal"])
    return {"schema_version":1,"review_id":"phase1-national-natural-editorial-candidates-v1","status":"REVIEW_ONLY_NOT_RUNTIME_OR_PUBLICATION_SOURCE","scope":"NATIONAL_CROSS_DESTINATION_EDITORIAL_REVIEW","source_provenance":{"governed_input_path":GOVERNED_RELATIVE,"governed_input_sha256":GOVERNED_SHA256,"governed_input_record_count":945,"external_audit_inputs":[{"basename":n,"sha256":h} for n,h in EXTERNAL_HASHES.items()],"absolute_source_path_recorded":False,"ordinary_validation_requires_external_inputs":False},"priority_scope":inventory["priority_scope"],"candidate_queues":queues,"evaluated_exclusions_and_deferrals":exclusions,"non_phase1_resolution_evidence":nonphase,"ordinal_resolution":inventory["ordinal_resolution"],"category_accounting":audit["category_accounting"],"global_accounting":audit["global_accounting"],"readiness_distribution":audit["readiness_distribution_eligible_candidates"],"score_distribution":audit["score_distribution_eligible_candidates"],"duplicate_conflict_findings":audit["quality_findings"],"score_policy":audit["score_policy"],"institutional_review_policy":{"dams_are_infrastructure_associated_not_purely_natural":True,"dam_requirements":["VERIFY_DAM_SAFETY_AND_OPERATIONAL_AUTHORITY","VERIFY_VISITOR_ACCESSIBILITY","VERIFY_INSTITUTIONAL_PRESENTATION_AUTHORITY"],"mountain_source_gap":True,"mountain_source_action":"FUTURE_GOVERNED_MOUNTAIN_SOURCE_ACQUISITION_REQUIRED","new_coast_or_beach_candidate_gap":True,"missing_descriptions_among_candidates":367,"usable_repository_media_among_candidates":0,"media_rights_cleared_among_candidates":0,"editorial_score_is_triage_not_approval":True},"publication_and_protected_invariants":{"green_mountain_curated_features":180,"libyan_sahara_curated_features":69,"curated_frontend_total":249,"national_publication_gis_count":214,"approval_ledger_empty":True,"registry_modified":False,"source_manifest_modified":False,"curated_layers_modified":False,"runtime_or_frontend_modified":False},"governance":{"review_only":True,"runtime_source":False,"publication_approved":False,"canonical_approval":False,"public_visibility_enabled":False,"publication_media_eligible":False,"institutional_review_status":"UNRESOLVED","canonical_destination":None,"editorial_selection_is_approval":False}}

def all_candidates(a:dict)->list[dict]:return [x for c in CATEGORIES for x in a.get("candidate_queues",{}).get(c,[])]
def validate_artifact(a:dict,root:Path=ROOT,check_git:bool=True)->dict:
    errors=[]
    def check(ok,msg):
        if not ok:errors.append(msg)
    check(a.get("schema_version")==1 and a.get("status")=="REVIEW_ONLY_NOT_RUNTIME_OR_PUBLICATION_SOURCE","schema/status mismatch")
    p=a.get("source_provenance",{});check(p.get("governed_input_path")==GOVERNED_RELATIVE and p.get("governed_input_sha256")==GOVERNED_SHA256 and p.get("governed_input_record_count")==945,"governed provenance mismatch");check({x.get("basename"):x.get("sha256") for x in p.get("external_audit_inputs",[])}==EXTERNAL_HASHES,"external hash provenance mismatch");check(p.get("absolute_source_path_recorded") is False and p.get("ordinary_validation_requires_external_inputs") is False,"source portability mismatch")
    try:governed=json.loads(committed_governed_bytes(root));sources=governed_records(governed)
    except (OSError,subprocess.CalledProcessError,Phase1EditorialError,json.JSONDecodeError) as exc:sources={};errors.append(str(exc))
    check(list(a.get("candidate_queues",{}))==list(CATEGORIES),"queue order mismatch");check({c:len(a.get("candidate_queues",{}).get(c,[])) for c in CATEGORIES}==EXPECTED_QUEUES,"eligible queue counts mismatch")
    candidates=all_candidates(a);check(len(candidates)==383,"candidate count mismatch");check(len({x.get("editorial_review_id") for x in candidates})==383,"candidate IDs not unique");check(Counter(x.get("editorial_priority_band") for x in candidates)==Counter({k:v for k,v in EXPECTED_PRIORITY.items() if v}),"priority distribution mismatch")
    for x in candidates:
        o=x.get("source_ordinal");check(x.get("editorial_review_id")==expected_editorial_id(x),f"deterministic ID mismatch {o}");check(x.get("eligibility_state")=="ELIGIBLE_NEW_EDITORIAL_CANDIDATE" and not x.get("exclusion_reasons"),f"ineligible queued candidate {o}");check(x.get("overlap_state")=="NO_INSPECTED_GOVERNED_OVERLAP",f"overlap queued {o}");check(x.get("clean_governed_record") is True and x.get("mandatory_display_exclusion") is False,f"governed eligibility mismatch {o}")
        coord=x.get("coordinates");check(isinstance(coord,list) and len(coord)==2 and all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in coord),f"invalid coordinate {o}")
        for field in FALSE_FIELDS:check(x.get(field) is False,f"candidate {o} grants {field}")
        check(x.get("institutional_review_status")=="UNRESOLVED" and x.get("canonical_destination") is None,f"candidate {o} canonical/institutional drift")
        source=sources.get(o,{});check(x.get("governed_review_id")==source.get("review_id"),f"governed linkage mismatch {o}");check(x.get("source_evidence")==source_evidence(source) if source else False,f"source evidence mismatch {o}")
        score=x.get("editorial_readiness_score",{});check(score.get("total")==sum(score.get(k,-1000) for k in ("identity_clarity","coordinate_quality","description_completeness","institutional_provenance","duplicate_conflict_safety","media_readiness_and_rights")),f"score mismatch {o}")
    check(sum(x.get("description_quality")=="MISSING" for x in candidates)==367,"candidate description gap mismatch");check(sum(x.get("media_availability")=="REPOSITORY_ASSET_AVAILABLE" for x in candidates)==0,"usable media unexpectedly present");check(sum(x.get("media_rights_status")!="NO_INDEPENDENT_RIGHTS_EVIDENCE" for x in candidates)==0,"media rights unexpectedly cleared")
    dams=a.get("candidate_queues",{}).get("DAMS_AND_RESERVOIRS_REVIEW",[]);required=set(a.get("institutional_review_policy",{}).get("dam_requirements",[]));check(len(dams)==23 and all(required<=set(x.get("required_human_review_actions",[])) for x in dams),"dam institutional requirements missing");check(a.get("institutional_review_policy",{}).get("dams_are_infrastructure_associated_not_purely_natural") is True,"dam nature safeguard missing")
    check(not a.get("candidate_queues",{}).get("MOUNTAINS_AND_HIGHLANDS") and not a.get("candidate_queues",{}).get("NATURAL_COASTS_AND_BEACHES"),"mountain/coast gap filled without evidence")
    repeat=sum(x.get("duplicate_conflict_state")=="SAME_NAME_DIFFERENT_COORDINATE" for x in candidates);near=sum(str(x.get("duplicate_conflict_state","")).startswith("NEAR_COORDINATE") for x in candidates);check(repeat==71 and near==3,"candidate conflict preservation mismatch")
    exclusions=a.get("evaluated_exclusions_and_deferrals",[]);nonphase=a.get("non_phase1_resolution_evidence",[]);check(len(exclusions)==293 and len(nonphase)==269,"noncandidate representation mismatch")
    resolution=a.get("ordinal_resolution",[]);check([x.get("source_ordinal") for x in resolution]==list(range(1,946)),"ordinal resolution mismatch");check(Counter(x.get("state") for x in resolution)==Counter(EXPECTED_RESOLUTION),"resolution counts mismatch")
    for key,value in EXPECTED_GLOBAL.items():check(a.get("global_accounting",{}).get(key)==value,f"global accounting drift {key}")
    mandatory={x.get("source_ordinal"):x.get("source_evidence",{}).get("raw_name") for x in nonphase if x.get("resolution_state")=="MANDATORY_DISPLAY_EXCLUSION"};check(mandatory==MANDATORY_NAMES,"mandatory exclusions mismatch")
    inv=a.get("publication_and_protected_invariants",{});check((inv.get("green_mountain_curated_features"),inv.get("libyan_sahara_curated_features"),inv.get("curated_frontend_total"),inv.get("national_publication_gis_count"))==(180,69,249,214),"protected count declaration mismatch")
    try:
        green=json.loads((root/"backend/data/gis/green-mountain-tourism-curated.review.json").read_text(encoding="utf-8"));sahara=json.loads((root/"backend/data/gis/libyan-sahara-tourism-curated.review.json").read_text(encoding="utf-8"));registry=json.loads((root/"backend/data/destinations/national-destination-registry.review.json").read_text(encoding="utf-8"));check(len(green["records"])==180 and len(sahara["records"])==69,"curated counts changed");check(sum(x.get("gis_record_count",0) for x in registry["records"])==214,"registry GIS count changed");check((root/"backend/data/governance/publication-approval-ledger.jsonl").stat().st_size==0,"approval ledger not empty")
    except (OSError,KeyError,json.JSONDecodeError) as exc:errors.append(f"protected invariant read failed: {exc}")
    for field in FALSE_FIELDS:check(a.get("governance",{}).get(field) is False,f"artifact grants {field}")
    if check_git:
        status=subprocess.run(["git","status","--porcelain=v1","--untracked-files=all"],cwd=root,check=True,capture_output=True,text=True,encoding="utf-8");changed={line[3:].replace("\\","/") for line in status.stdout.splitlines() if len(line)>=4};check(changed<=ALLOWED_CHANGED,f"changed-file allowlist violation: {sorted(changed-ALLOWED_CHANGED)}")
        protected=subprocess.run(["git","diff","--name-only","HEAD","--",*PROTECTED],cwd=root,check=True,capture_output=True,text=True,encoding="utf-8");check(not protected.stdout.strip(),f"protected paths changed: {protected.stdout.strip()}")
    if errors:raise Phase1EditorialError("\n".join(errors))
    return {"governed_ordinals":945,"evaluated":676,"eligible_candidates":383,"excluded_or_deferred":562,"queues":EXPECTED_QUEUES}

def validate_serialization(path:Path=ARTIFACT_PATH):
    raw=path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r\n" in raw or not raw.endswith(b"\n") or raw.endswith(b"\n\n"):raise Phase1EditorialError("artifact must be UTF-8 without BOM, LF, and one final newline")
    if re.search(rb"[A-Za-z]:\\",raw) or b"visitlibya-local-backups" in raw:raise Phase1EditorialError("artifact contains absolute/local path")

def main()->int:
    try:
        if len(sys.argv)==3 and sys.argv[1]=="build":
            artifact=build_artifact(Path(sys.argv[2]));ARTIFACT_PATH.write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
        elif len(sys.argv)!=1:raise Phase1EditorialError("usage: phase1_natural_editorial_candidates.py [build EXTERNAL_AUDIT_DIRECTORY]")
        validate_serialization();result=validate_artifact(json.loads(ARTIFACT_PATH.read_text(encoding="utf-8")));print("Phase 1 natural editorial candidate validation passed: "+json.dumps(result,sort_keys=True));return 0
    except (OSError,json.JSONDecodeError,subprocess.CalledProcessError,Phase1EditorialError) as exc:print(f"Phase 1 natural editorial candidate validation failed: {exc}",file=sys.stderr);return 1
if __name__=="__main__":raise SystemExit(main())

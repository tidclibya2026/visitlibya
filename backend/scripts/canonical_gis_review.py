from __future__ import annotations

import html
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

from scripts.gis_registry import NormalizedFeature, SourceAudit, SourceSpec

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
BIDI_RE = re.compile(r"[\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]")
DIACRITIC_RE = re.compile(r"[\u064b-\u065f\u0670]")


@dataclass(frozen=True)
class ReviewProfile:
    aliases: tuple[str, ...]
    aggregate: bool = False


PROFILES: dict[str, ReviewProfile] = {
    "leptis-magna": ReviewProfile(("Leptis Magna", "Leptis", "لبدة الكبرى", "لبتس ماغنا", "لبدة")),
    "sabratha": ReviewProfile(("Sabratha", "صبراتة")),
    "ghadames": ReviewProfile(("Ghadames", "غدامس", "مدينة غدامس القديمة")),
    "acacus": ReviewProfile(("Tadrart Acacus", "Acacus", "تادرارت أكاكوس", "تدرارت أكاكوس", "أكاكوس", "اكاكوس"), True),
    "tripoli": ReviewProfile(("Tripoli Old City", "Old Tripoli", "المدينة القديمة طرابلس", "طرابلس القديمة", "المدينة القديمة")),
    "green-mountain": ReviewProfile(("Jebel Akhdar", "Green Mountain", "الجبل الأخضر"), True),
    "bomba-bay": ReviewProfile(("Bomba Bay", "خليج بمبة")),
    "awjila": ReviewProfile(("Awjila", "أوجلة", "اوجلة")),
    "nafusa": ReviewProfile(("Nafusa Mountains", "Nafusa", "جبل نفوسة", "نفوسة"), True),
    "desert": ReviewProfile(("The Libyan Sahara", "Libyan Sahara", "الصحراء الليبية"), True),
    "benghazi": ReviewProfile(("Benghazi", "بنغازي")),
    "villa-sileen": ReviewProfile(("Villa Sileen", "Villa Silin", "فيلا سيلين", "سيلين")),
}


def semantic_normalize(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    text = DIACRITIC_RE.sub("", BIDI_RE.sub("", text)).casefold()
    text = "".join(character if character.isalnum() else " " for character in text)
    return SPACE_RE.sub(" ", text).strip()


def description_excerpt(value: str | None, limit: int = 300) -> str | None:
    if not value:
        return None
    cleaned = SPACE_RE.sub(" ", TAG_RE.sub(" ", html.unescape(value))).strip()
    return cleaned[:limit] + ("…" if len(cleaned) > limit else "")


def _search_fields(feature: NormalizedFeature) -> dict[str, str]:
    property_text = " ".join(str(value) for value in feature.properties.values() if value not in (None, ""))
    return {
        "name": " ".join(filter(None, (feature.raw_name, feature.name_ar, feature.name_en))),
        "description": feature.description or "",
        "category": feature.category or "",
        "locality": feature.locality or "",
        "region": feature.region or "",
        "context": " / ".join(feature.context_path),
        "properties": property_text,
    }


def discovery_evidence(profile: ReviewProfile, feature: NormalizedFeature) -> tuple[float, list[str]] | None:
    fields = _search_fields(feature)
    normalized = {key: semantic_normalize(value) for key, value in fields.items()}
    aliases = [semantic_normalize(alias) for alias in profile.aliases]
    reasons: list[str] = []
    score = 0.0
    for alias in aliases:
        if not alias:
            continue
        if normalized["name"] == alias:
            score = max(score, 1.0); reasons.append("exact normalized source name")
        elif len(alias) >= 4 and (alias in normalized["name"] or normalized["name"] in alias) and normalized["name"]:
            score = max(score, 0.9 + min(len(alias), 50) / 1000); reasons.append("canonical/source alias occurs in source name")
        else:
            similarity = SequenceMatcher(None, alias, normalized["name"]).ratio() if normalized["name"] else 0
            if similarity >= 0.72:
                score = max(score, round(similarity, 4)); reasons.append("source-name similarity for discovery only")
        for field in ("context", "locality", "region", "category"):
            if len(alias) >= 4 and alias in normalized[field]:
                score = max(score, 0.7); reasons.append(f"alias present in source {field}")
        if len(alias) >= 5 and alias in normalized["description"]:
            score = max(score, 0.7); reasons.append("alias present in source description")
        if len(alias) >= 5 and alias in normalized["properties"]:
            score = max(score, 0.6); reasons.append("alias present in source properties")
    if score < 0.68:
        return None
    return score, sorted(set(reasons))


def _destination_relevant(slug: str, feature: NormalizedFeature, reasons: list[str]) -> bool:
    name = semantic_normalize(feature.raw_name)
    if slug == "tripoli":
        old_city_terms = ("المدينة القديمة", "طرابلس القديمة", "tripoli old city", "old tripoli")
        return feature.source_id == "tripoli-old-city" and any(semantic_normalize(term) in name for term in old_city_terms)
    allowed = (
        "exact normalized source name", "canonical/source alias occurs in source name",
        "source-name similarity for discovery only", "alias present in source locality",
        "alias present in source region", "alias present in source category",
    )
    if slug == "desert":
        allowed += ("alias present in source description", "alias present in source properties")
    return any(reason in reasons for reason in allowed)


def _facility_context(feature: NormalizedFeature, spec: SourceSpec) -> bool:
    context = semantic_normalize(" ".join(filter(None, (feature.raw_name, feature.category, spec.dataset_role))))
    return any(term in context for term in ("hotel", "فندق", "cafe", "مقهى", "restaurant", "مطعم", "resort", "منتجع", "قرية سياحية"))


def _semantic_scope(slug: str, feature: NormalizedFeature, reasons: list[str]) -> str:
    name = semantic_normalize(feature.raw_name)
    destination_level_names = {
        "acacus": ("مواقع تادرارت أكاكوس الصخرية",),
        "leptis-magna": ("موقع لبدة الأثري",),
        "sabratha": ("موقع صبراتة الأثري",),
        "ghadames": ("مدينة غدامس القديمة",),
        "bomba-bay": ("خليج بمبة",),
    }
    if any(semantic_normalize(value) in name for value in destination_level_names.get(slug, ())):
        return "DESTINATION_LEVEL_FEATURE"
    if any(term in name for term in ("مدخل", "نقطة مراقبة", "مركز زوار", "visitor center", "بوابة")):
        return "INSTITUTIONAL_ANCHOR"
    if any(reason in reasons for reason in ("alias present in source region", "alias present in source description", "alias present in source properties")) and not any(
        reason in reasons for reason in ("exact normalized source name", "canonical/source alias occurs in source name")
    ):
        return "REGIONAL_CONTEXT"
    return "SUB_FEATURE"


def _candidate_status(slug: str, feature: NormalizedFeature, spec: SourceSpec, scope: str) -> tuple[str, str]:
    name = semantic_normalize(feature.raw_name)
    if slug == "acacus" and feature.source_id == "unesco-five-sites-ly" and scope == "DESTINATION_LEVEL_FEATURE":
        return "APPROVAL_READY", "UNESCO source explicitly names the Tadrart Acacus rock-art sites as a destination-level heritage feature; human approval is still required"
    if slug == "leptis-magna" and feature.source_id == "unesco-five-sites-ly" and semantic_normalize("موقع لبدة الأثري") in name:
        return "APPROVAL_READY", "source explicitly names the Leptis archaeological site at destination level; human approval is still required"
    if slug == "sabratha" and feature.source_id == "unesco-five-sites-ly" and semantic_normalize("موقع صبراتة الأثري") in name:
        return "APPROVAL_READY", "source explicitly names the Sabratha archaeological site at destination level; human approval is still required"
    if slug == "ghadames" and feature.source_id == "unesco-five-sites-ly" and semantic_normalize("مدينة غدامس القديمة") in name:
        return "APPROVAL_READY", "source explicitly names Old Ghadames at site/city level; competing site-level points must be resolved by human review"
    if slug == "bomba-bay" and feature.source_id == "natural-atlas-media" and name == semantic_normalize("خليج بمبة"):
        return "APPROVAL_READY", "Natural Atlas enriched feature explicitly names Bomba Bay and retains proven base-source lineage"
    if PROFILES.get(slug, ReviewProfile(())).aggregate:
        scope_label = scope.lower().replace("_", " ")
        return "REVIEW_REQUIRED_AGGREGATE", f"canonical destination is broad and this evidence is {scope_label}; human review must establish an approved representative point"
    if _facility_context(feature, spec):
        return "REVIEW_REQUIRED", "same-place terminology occurs in a facility record; it must not represent the canonical destination without human evidence"
    return "REVIEW_REQUIRED", "source is semantically related but identity and representative-point suitability require human review"


def build_canonical_review(
    canonical: list[dict[str, Any]],
    features: list[NormalizedFeature],
    specs: dict[str, SourceSpec],
    audits: dict[str, SourceAudit],
) -> dict[str, Any]:
    destinations: list[dict[str, Any]] = []
    all_candidates: list[dict[str, Any]] = []
    for destination in canonical:
        slug = destination["slug"]
        profile = PROFILES.get(slug, ReviewProfile(tuple(filter(None, (destination.get("name_ar"), destination.get("name_en"))))))
        found: list[tuple[float, NormalizedFeature, list[str]]] = []
        for feature in features:
            evidence = discovery_evidence(profile, feature)
            if evidence and _destination_relevant(slug, feature, evidence[1]):
                found.append((evidence[0], feature, evidence[1]))
        status_priority = {"APPROVAL_READY": 0, "AMBIGUOUS": 1, "REVIEW_REQUIRED_AGGREGATE": 2, "REVIEW_REQUIRED": 3}
        found.sort(key=lambda row: (
            status_priority.get(_candidate_status(slug, row[1], specs[row[1].source_id], _semantic_scope(slug, row[1], row[2]))[0], 9),
            _facility_context(row[1], specs[row[1].source_id]),
            -row[0], row[1].source_id, row[1].source_index,
        ))
        candidates: list[dict[str, Any]] = []
        for rank, (score, feature, discovery_reasons) in enumerate(found, 1):
            spec, audit = specs[feature.source_id], audits[feature.source_id]
            scope = _semantic_scope(slug, feature, discovery_reasons)
            status, semantic_reason = _candidate_status(slug, feature, spec, scope)
            candidate = {
                "destination_slug": slug,
                "canonical_name_ar": destination.get("name_ar"),
                "canonical_name_en": destination.get("name_en"),
                "source_id": feature.source_id,
                "source_file": spec.expected_filename,
                "source_sha256": audit.sha256,
                "source_feature_id": feature.feature_id,
                "source_native_id": feature.source_feature_id,
                "source_name": feature.raw_name,
                "source_description_excerpt": description_excerpt(feature.description),
                "category_context": {
                    "category": feature.category, "locality": feature.locality, "region": feature.region,
                    "folder_document_path": feature.context_path, "dataset_role": spec.dataset_role,
                },
                "longitude": feature.longitude,
                "latitude": feature.latitude,
                "geometry_type": feature.geometry_types,
                "match_status": status,
                "semantic_scope": scope,
                "match_reason": semantic_reason,
                "discovery_rank": rank,
                "discovery_similarity": score,
                "discovery_reasons": discovery_reasons,
                "source_reference": feature.source_reference,
                "related_sources": feature.related_sources,
            }
            candidates.append(candidate); all_candidates.append(candidate)
        site_candidates = [item for item in candidates if item["match_status"] == "APPROVAL_READY"]
        if len(site_candidates) > 1:
            coordinate_pairs = {(item["longitude"], item["latitude"]) for item in site_candidates}
            if len(coordinate_pairs) > 1:
                for item in site_candidates:
                    item["match_status"] = "AMBIGUOUS"
                    item["match_reason"] += "; multiple competing destination-level coordinate pairs exist"
        if site_candidates and all(item["match_status"] == "APPROVAL_READY" for item in site_candidates):
            summary_status = "APPROVAL_READY"
        elif any(item["match_status"] == "AMBIGUOUS" for item in candidates):
            summary_status = "AMBIGUOUS"
        elif candidates and profile.aggregate:
            summary_status = "REVIEW_REQUIRED_AGGREGATE"
        elif candidates:
            summary_status = "REVIEW_REQUIRED"
        else:
            summary_status = "NO_MATCH"
        best = candidates[0] if candidates else None
        scopes = {item["semantic_scope"] for item in candidates}
        destinations.append({
            **destination,
            "review_status": summary_status,
            "representation_findings": {
                "explicit_destination_level_feature": "DESTINATION_LEVEL_FEATURE" in scopes,
                "institutional_anchor": "INSTITUTIONAL_ANCHOR" in scopes,
                "sub_features": "SUB_FEATURE" in scopes,
                "regional_context": "REGIONAL_CONTEXT" in scopes,
                "multiple_competing_destination_candidates": len({
                    (item["longitude"], item["latitude"])
                    for item in candidates if item["semantic_scope"] == "DESTINATION_LEVEL_FEATURE"
                }) > 1,
            },
            "best_candidate": {
                "source_id": best["source_id"], "source_feature_id": best["source_feature_id"],
                "source_name": best["source_name"], "longitude": best["longitude"], "latitude": best["latitude"],
                "semantic_scope": best["semantic_scope"], "match_status": best["match_status"], "reason": best["match_reason"],
            } if best else None,
            "candidate_count": len(candidates),
            "candidates": candidates,
        })
    status_counts: dict[str, int] = defaultdict(int)
    for destination in destinations:
        status_counts[destination["review_status"]] += 1
    return {
        "schema_version": 1,
        "artifact_status": "HUMAN_REVIEW_ONLY_NOT_COORDINATE_APPROVAL",
        "classification_policy": "similarity ranks discovery only; no candidate is automatically approved",
        "summary": {"canonical_destinations": len(destinations), "candidates": len(all_candidates), "destination_status_counts": dict(sorted(status_counts.items()))},
        "destinations": destinations,
    }

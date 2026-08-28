# ARCHAEOLOGICAL_SITES governed layer

## Scope

This layer contains only net-new archaeological review candidates from the
`اثري` feature class in `Libya ATLAS Project.gdb`.

The Master Atlas Source Registry v2 identifies exactly 11 source Points for
this review route.

Previously governed authorities are not rebuilt here.

## Authority separation

The following remain independent governed authorities or review domains:

- WORLD_HERITAGE
- OLD_TRIPOLI
- NATURAL_SITES
- Cyrene/Shahat governed review evidence
- Ghadames governed review evidence
- Leptis Magna heritage scope
- Sabratha heritage scope
- Acacus World Heritage authority

Overlap with WORLD_HERITAGE is blocked as cross-layer context rather than
creating duplicate archaeological authority.

## Governance state

All ingestible features remain:

- review_status = under_review
- authority_status = unapproved
- validation_status = valid
- is_validated = true
- is_published = false

No archaeological boundary, excavation extent, property boundary, UNESCO
boundary, protection zone, or buffer zone is inferred.

## Regeneration

python backend/scripts/archaeological_sites_governed_layer.py --write
python backend/scripts/archaeological_sites_governed_layer.py

## Tests

python -m pytest -q backend/tests/unit/scripts/test_archaeological_sites_governed_layer.py

import json
from scripts import cafes_governed_layer as layer
from scripts import ingest_governed_gis as ingestion

def test_cafes_accounting_and_governance():
    source, imported, blocked, cross=layer.validate()
    assert len(source['features'])==416
    assert len(imported['features'])+len(blocked['records'])==416
    assert all(x['publication_approved'] is False for x in (source,imported,blocked,cross))
def test_cafes_sources_preserved():
    source,*_=layer.validate(); assert source['gdb_feature_count']==12; assert source['kml_feature_count']==404
    assert {f['geometry']['type'] for f in source['features']}=={'Point'}
def test_cafes_ingestion_contract(tmp_path):
    _,imported,_,_=layer.build(); p=tmp_path/'cafes.geojson';p.write_text(json.dumps(imported,ensure_ascii=False),encoding='utf-8')
    validated=ingestion.validate_geojson(p,'CAFES');assert len(validated.features)==len(imported['features']);assert {x.geometry_type for x in validated.features}=={'POINT'}
def test_cross_layer_relationships_are_not_authority():
    *_,cross=layer.validate(); assert cross['authoritative_boundary_claimed'] is False
    assert all(x['relationship']=='CROSS_LAYER_REFERENCE' for x in cross['records'])



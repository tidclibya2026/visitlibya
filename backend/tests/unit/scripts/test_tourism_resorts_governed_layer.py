import json
from scripts import tourism_resorts_governed_layer as layer
from scripts import ingest_governed_gis as ingestion
def test_accounting():
 s,i,b,c=layer.validate();assert len(s['features'])==433;assert len(i['features'])+len(b['records'])==433;assert all(x['publication_approved'] is False for x in (s,i,b,c))
def test_sources_and_polygons_preserved():
 s,*_=layer.validate();assert s['gdb_feature_count']==171 and s['kml_feature_count']==262;assert sum(f['geometry']['type']=='Polygon' for f in s['features'])==6
def test_ingestion(tmp_path):
 _,i,_,_=layer.build();p=tmp_path/'resorts.geojson';p.write_text(json.dumps(i,ensure_ascii=False),encoding='utf-8');v=ingestion.validate_geojson(p,'TOURISM_RESORTS');assert len(v.features)==len(i['features'])
def test_cross_layer_is_reference_only():
 *_,c=layer.validate();assert all(x['relationship']=='CROSS_LAYER_REFERENCE' for x in c['records']);assert c['authoritative_boundary_claimed'] is False

#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,math,xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from pathlib import Path
from shapely.geometry import shape
from scripts import hotels_governed_layer as h

ROOT=Path(__file__).resolve().parents[2];GIS=ROOT/'backend/data/gis';ATLAS=ROOT/'atlas'
GDB=GIS/'tourism-resorts-gdb-source.review.geojson';KML=ATLAS/'القرى_والمنتجعات السياحية_LY.kml';SOURCE=GIS/'tourism-resorts-source.review.geojson';IMPORT=GIS/'tourism-resorts-governed-import.review.geojson';BLOCKED=GIS/'tourism-resorts-governed-blocked.review.json';CROSS=GIS/'tourism-resorts-cross-layer-review.json'
HASH='e1e923949a79c6aeb59f80687c669979134682a17b57e3a940e2303a69054449';STATUS=h.STATUS;LAYER='TOURISM_RESORTS'
class TourismResortsError(ValueError):pass
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def canon(x):return h.canon(x)
def parse_kml():
 if hashlib.sha256(KML.read_bytes()).hexdigest()!=HASH:raise TourismResortsError('KML hash mismatch')
 root=ET.fromstring(KML.read_bytes());parents={c:p for p in root.iter() for c in p};out=[]
 for i,pm in enumerate((x for x in root.iter() if h.lname(x.tag)=='Placemark'),1):
  gs=[x for x in list(pm) if h.lname(x.tag) in {'Point','Polygon','MultiGeometry','LineString'}]
  if len(gs)!=1 or h.lname(gs[0].tag)!='Point':raise TourismResortsError(f'Unexpected KML geometry {i}')
  cn=next((x for x in gs[0].iter() if h.lname(x.tag)=='coordinates'),None);v=(h.text(cn) or '').split(',');g={'type':'Point','coordinates':[float(v[0]),float(v[1])]}
  ex={}
  for x in pm.iter():
   if h.lname(x.tag)=='Data' and x.get('name'):ex[x.get('name')]=h.text(h.child(x,'value'))
   elif h.lname(x.tag)=='SimpleData' and x.get('name'):ex[x.get('name')]=h.text(x)
  folders=[];a=parents.get(pm)
  while a is not None:
   if h.lname(a.tag) in {'Folder','Document'} and h.text(h.child(a,'name')):folders.append(h.text(h.child(a,'name')))
   a=parents.get(a)
  out.append({'type':'Feature','properties':{'authority_status':'UNAPPROVED','governance_role':'LATEST_SUPPLIED_SNAPSHOT','is_published':False,'publication_approved':False,'canonical_identity_approved':False,'authoritative_boundary_claimed':False,'source_attributes':{'Name':h.text(h.child(pm,'name')),'description':h.text(h.child(pm,'description')),'extended_data':ex,'kml_context_path':list(reversed(folders))},'source_composite_id':f'KML_D81FB3F680:Placemark-{i}','source_database':'القرى_والمنتجعات السياحية_LY.kml','source_filename_registry':'القرى_والمنتجعات السياحية_LY(1).kml','source_feature_id':f'Placemark-{i}','source_id':'KML_D81FB3F680','source_layer':'القرى_والمنتجعات السياحية_LY(1)','source_subtype':'tourism_resort_kml','target_layer':LAYER},'geometry':g})
 if len(out)!=262:raise TourismResortsError('Expected 262 KML features')
 return out
def combined():
 g=load(GDB)
 if len(g.get('features',[]))!=171:raise TourismResortsError('Expected 171 GDB features')
 return {'type':'FeatureCollection','schema_version':1,'artifact_status':'SOURCE_REVIEW_ONLY_NOT_PUBLICATION_APPROVAL','layer_code':LAYER,'source_feature_count':433,'extracted_feature_count':433,'gdb_feature_count':171,'kml_feature_count':262,'source_kml_sha256':HASH,'publication_approved':False,'canonical_identity_approved':False,'authoritative_boundary_claimed':False,'features':g['features']+parse_kml()}
def cross_index():
 idx=defaultdict(list);specs=[('HOTELS',GIS/'hotels-governed-import.review.geojson'),('PARKS',GIS/'parks-governed-import.review.geojson'),('TOURISM_INVESTMENT',GIS/'tourism-investment-gdb-source.review.geojson')]
 for code,p in specs:
  if not p.is_file():continue
  for f in load(p).get('features',[]):
   g=f.get('geometry') or {}
   if g.get('type')=='Point' and h.valid(g):idx[h.pkey(g)].append({'layer_code':code,'source_feature_id':f.get('properties',{}).get('source_feature_id'),'name_ar':f.get('properties',{}).get('name_ar')})
 return idx
def build(source=None):
 src=source or load(SOURCE)
 if len(src.get('features',[]))!=433 or src.get('source_kml_sha256')!=HASH:raise TourismResortsError('Source accounting mismatch')
 rows=[];ids=Counter();coordnames=defaultdict(set)
 for f in src['features']:
  p=f['properties'];n=h.attrs_name(p.get('source_attributes') or {});nn=h.norm(n);g=f.get('geometry') or {};key=h.pkey(g) if g.get('type')=='Point' and h.valid(g) else None;sig=json.dumps(g,sort_keys=True,separators=(',',':'))
  if nn:ids[(nn,sig)]+=1
  if key:coordnames[key].add(nn)
  rows.append((f,n,nn,key,sig))
 idx=cross_index();safe=[];blocked=[];cross=[]
 for f,n,nn,key,sig in rows:
  p=f['properties'];g=f.get('geometry') or {};matches=idx.get(key,[]) if key else [];cls='SAFE_TOURISM_RESORT_GEOMETRY'
  try:s=shape(g);good=g.get('type') in {'Point','Polygon','MultiPolygon'} and s.is_valid and not s.is_empty and all(math.isfinite(x) for x in s.bounds) and s.bounds[0]>=-180 and s.bounds[2]<=180 and s.bounds[1]>=-90 and s.bounds[3]<=90
  except Exception:good=False
  if not good:cls='SOURCE_GEOMETRY_CRS_REVIEW'
  elif not nn:cls='SOURCE_IDENTITY_REVIEW'
  elif ids[(nn,sig)]>1:cls='EXACT_DUPLICATE_IDENTITY_GEOMETRY_REVIEW'
  elif key and len(coordnames[key])>1:cls='SAME_GEOMETRY_DIFFERENT_IDENTITY_REVIEW'
  elif matches:cls='CROSS_LAYER_REFERENCE'
  seed=str(p.get('source_composite_id') or f"{p.get('source_id')}:{p.get('source_layer')}:{p.get('source_feature_id')}");iid='atlas-resort-'+hashlib.sha256(seed.encode()).hexdigest()[:20];st=p.get('source_subtype') or p.get('source_layer');meta={'artifact_status':STATUS,'review_classification':cls,'source_id':p.get('source_id'),'source_database':p.get('source_database'),'source_layer':p.get('source_layer'),'source_subtype':st,'source_feature_id':str(p.get('source_feature_id')),'source_composite_id':p.get('source_composite_id'),'source_attributes':p.get('source_attributes') or {},'publication_approved':False,'canonical_identity_approved':False,'authoritative_boundary_claimed':False,'cross_layer_authority_created':False};rec={'institutional_id':iid,'source_feature_id':str(p.get('source_feature_id')),'source_layer':p.get('source_layer'),'resort_subtype':st,'name_ar':n,'review_classification':cls,'geometry_type':g.get('type'),'geometry':g,'source_metadata':meta}
  if matches:cross.append({'resort_institutional_id':iid,'resort_name_ar':n,'coordinate':list(key),'relationship':'CROSS_LAYER_REFERENCE','matches':matches,'publication_approved':False})
  if cls=='SAFE_TOURISM_RESORT_GEOMETRY':safe.append({'type':'Feature','properties':{'feature_code':iid,'institutional_id':iid,'source_feature_id':str(p.get('source_feature_id')),'name_ar':n,'name_en':None,'category':'tourism_resort','resort_subtype':st,'review_classification':cls,'source_identity':f"{p.get('source_database')}#{p.get('source_layer')}-{p.get('source_feature_id')}",'source_metadata':meta},'geometry':g})
  else:rec['blocked_reason']=cls;blocked.append(rec)
 counts=Counter(['SAFE_TOURISM_RESORT_GEOMETRY']*len(safe));counts.update(x['review_classification'] for x in blocked);common={'artifact_status':STATUS,'layer_code':LAYER,'source_feature_count':433,'publication_approved':False,'canonical_identity_approved':False,'authoritative_boundary_claimed':False,'category_counts':dict(sorted(counts.items())),'source_kml_sha256':HASH}
 return src,{'type':'FeatureCollection','name':'TOURISM_RESORTS governed review import',**common,'features':safe},{'schema_version':1,'inventory_id':'tourism-resorts-governed-blocked-v1',**common,'safe_ingestible_feature_count':len(safe),'blocked_feature_count':len(blocked),'records':blocked},{'schema_version':1,'inventory_id':'tourism-resorts-cross-layer-review-v1','artifact_status':STATUS,'layer_code':LAYER,'comparison_layers':['HOTELS','PARKS','TOURISM_INVESTMENT_GDB_ONLY'],'cross_layer_reference_count':len(cross),'publication_approved':False,'canonical_identity_approved':False,'authoritative_boundary_claimed':False,'records':cross}
def validate():
 b=build()
 for p,x in zip((SOURCE,IMPORT,BLOCKED,CROSS),b):
  if not p.is_file() or p.read_bytes()!=canon(x):raise TourismResortsError(f'Missing or stale {p.name}')
 if len(b[1]['features'])+len(b[2]['records'])!=433:raise TourismResortsError('Accounting failed')
 return b
def main():
 a=argparse.ArgumentParser();a.add_argument('--write',action='store_true');z=a.parse_args()
 if z.write:
  s=combined();SOURCE.write_bytes(canon(s))
  for p,x in zip((IMPORT,BLOCKED,CROSS),build(s)[1:]):p.write_bytes(canon(x))
 _,i,b,c=validate();print('SOURCE:',i['source_feature_count'],'SAFE:',len(i['features']),'BLOCKED:',len(b['records']),'CROSS:',len(c['records']));print(json.dumps(i['category_counts'],ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()

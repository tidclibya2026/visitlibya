#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json, math, re, unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; GIS=ROOT/'backend/data/gis'; ATLAS=ROOT/'atlas'
GDB=GIS/'cafes-gdb-source.review.geojson'; KML=ATLAS/'المقاهي_طرابلس.kml'
SOURCE=GIS/'cafes-source.review.geojson'; IMPORT=GIS/'cafes-governed-import.review.geojson'
BLOCKED=GIS/'cafes-governed-blocked.review.json'; CROSS=GIS/'cafes-cross-layer-review.json'
MASTER=GIS/'master-atlas-source-registry.v2.json'; LAYER='CAFES'; EXPECTED_HASH='e1d862175e6d8e05e7ef19404caf6ea1c3098b466ddcedf55a4cd233205a45e9'
STATUS='GOVERNED_REVIEW_IMPORT_ONLY_NOT_PUBLICATION_APPROVAL'

class CafesGovernedLayerError(ValueError): pass
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def canon(x): return (json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def lname(tag): return tag.rsplit('}',1)[-1]
def text(e):
    if e is None:return None
    v=''.join(e.itertext()).strip();return v or None
def child(e,n): return next((x for x in e if lname(x.tag)==n),None)
def norm(v):
    v=unicodedata.normalize('NFKC',str(v or ''))
    for c in '\u200e\u200f\u202a\u202b\u202c\ufeff':v=v.replace(c,'')
    return re.sub(r'[\s_-]+',' ',v.strip().lower()).strip()
def pkey(g): return tuple(round(float(v),7) for v in g['coordinates'][:2])
def valid(g):
    try:x,y=map(float,g['coordinates'][:2]);return all(math.isfinite(v) for v in (x,y)) and -180<=x<=180 and -90<=y<=90
    except (KeyError,TypeError,ValueError):return False
def attrs_name(a):
    for k in ('name_ar','Name_AR','ar_name','الاسم_العربي_للمرفق','name','Name','NAME','الاسم','اسم'):
        if a.get(k) not in (None,''):return str(a[k]).strip()
    return None

def parse_kml():
    if digest(KML)!=EXPECTED_HASH: raise CafesGovernedLayerError('CAFES KML hash mismatch')
    root=ET.fromstring(KML.read_bytes()); parents={c:p for p in root.iter() for c in p}
    out=[]
    for i,pm in enumerate((x for x in root.iter() if lname(x.tag)=='Placemark'),1):
        geoms=[x for x in list(pm) if lname(x.tag) in {'Point','Polygon','LineString','MultiGeometry'}]
        if len(geoms)!=1 or lname(geoms[0].tag)!='Point': raise CafesGovernedLayerError(f'Unexpected CAFES KML geometry at Placemark {i}')
        cn=next((x for x in geoms[0].iter() if lname(x.tag)=='coordinates'),None); parts=(text(cn) or '').split(',')
        if len(parts)<2: geometry={'type':'Point','coordinates':[]}
        else: geometry={'type':'Point','coordinates':[float(parts[0]),float(parts[1])]}
        props={}
        for x in pm.iter():
            if lname(x.tag)=='Data' and x.get('name'):props[x.get('name')]=text(child(x,'value'))
            elif lname(x.tag)=='SimpleData' and x.get('name'):props[x.get('name')]=text(x)
        folders=[]; anc=parents.get(pm)
        while anc is not None:
            if lname(anc.tag) in {'Folder','Document'} and text(child(anc,'name')):folders.append(text(child(anc,'name')))
            anc=parents.get(anc)
        name=text(child(pm,'name')); desc=text(child(pm,'description'))
        out.append({'type':'Feature','properties':{'authority_status':'UNAPPROVED','governance_role':'LATEST_SUPPLIED_SNAPSHOT','is_published':False,'is_validated':False,'publication_approved':False,'review_status':'REVIEW_REQUIRED','source_attributes':{'Name':name,'description':desc,'extended_data':props,'kml_context_path':list(reversed(folders))},'source_composite_id':f'KML_280D1EFE0E:Placemark-{i}','source_database':'المقاهي_طرابلس.kml','source_filename_registry':'المقاهي_طرابلس(1).kml','source_feature_id':f'Placemark-{i}','source_id':'KML_280D1EFE0E','source_layer':'المقاهي_طرابلس(1)','source_subtype':'cafe_kml','target_layer':LAYER,'validation_status':'SOURCE_EXTRACTED','canonical_identity_approved':False,'authoritative_boundary_claimed':False},'geometry':geometry})
    if len(out)!=404:raise CafesGovernedLayerError('Expected 404 CAFES KML placemarks')
    return out

def combined():
    g=load(GDB); k=parse_kml()
    if len(g.get('features',[]))!=12:raise CafesGovernedLayerError('Expected 12 CAFES GDB features')
    features=g['features']+k
    return {'type':'FeatureCollection','schema_version':1,'artifact_status':'SOURCE_REVIEW_ONLY_NOT_PUBLICATION_APPROVAL','layer_code':LAYER,'source_feature_count':416,'extracted_feature_count':416,'gdb_feature_count':12,'kml_feature_count':404,'source_database':['Libya ATLAS Project.gdb','المقاهي_طرابلس.kml'],'source_kml_sha256':EXPECTED_HASH,'publication_approved':False,'canonical_identity_approved':False,'authoritative_boundary_claimed':False,'features':features}

def comparison_coords():
    coords=defaultdict(list)
    specs=[('RESTAURANTS',GIS/'restaurants-governed-import.review.geojson')]
    for code,path in specs:
        if not path.is_file():
            continue
        for f in load(path).get('features',[]):
            g=f.get('geometry') or {}
            if g.get('type')=='Point' and valid(g):coords[pkey(g)].append({'layer_code':code,'source_layer':f.get('properties',{}).get('source_layer'),'source_feature_id':f.get('properties',{}).get('source_feature_id')})
    return coords

def build(source=None):
    src=source or load(SOURCE)
    if len(src.get('features',[]))!=416 or src.get('source_kml_sha256')!=EXPECTED_HASH:
        raise CafesGovernedLayerError('Combined CAFES source accounting or KML identity mismatch')
    rows=[]; identities=Counter(); coord_names=defaultdict(set)
    for f in src['features']:
        p=f['properties']; name=attrs_name(p.get('source_attributes') or {}); n=norm(name); g=f.get('geometry') or {}; key=pkey(g) if g.get('type')=='Point' and valid(g) else None
        if n and key:identities[(n,key)]+=1;coord_names[key].add(n)
        rows.append((f,name,n,key))
    crossidx=comparison_coords(); safe=[]; blocked=[]; crosses=[]
    for f,name,n,key in rows:
        p=f['properties']; sid=str(p['source_feature_id']); sl=p['source_layer']; st=p.get('source_subtype') or {'المقاهي_السياحية':'tourism_cafe'}.get(sl,'cafe'); matches=crossidx.get(key,[]) if key else []
        cls='SAFE_CAFE_POINT'
        if f.get('geometry',{}).get('type')!='Point' or key is None:cls='SOURCE_GEOMETRY_CRS_REVIEW'
        elif not n:cls='SOURCE_IDENTITY_REVIEW'
        elif n in {'مقهى','مقاهي','cafe'}:cls='GENERIC_NAME_IDENTITY_REVIEW'
        elif identities[(n,key)]>1:cls='EXACT_DUPLICATE_IDENTITY_GEOMETRY_REVIEW'
        elif len(coord_names[key])>1:cls='SAME_GEOMETRY_DIFFERENT_IDENTITY_REVIEW'
        elif matches:cls='CROSS_LAYER_REFERENCE'
        identity_seed=str(p.get('source_composite_id') or f"{p['source_id']}:{sl}:{sid}")
        iid=f"atlas-cafe-{hashlib.sha256(identity_seed.encode('utf-8')).hexdigest()[:20]}"
        meta={'artifact_status':STATUS,'review_classification':cls,'source_id':p['source_id'],'source_database':p['source_database'],'source_layer':sl,'source_subtype':st,'source_feature_id':sid,'source_composite_id':p.get('source_composite_id'),'source_attributes':p.get('source_attributes') or {},'publication_approved':False,'canonical_identity_approved':False,'authoritative_boundary_claimed':False,'cross_layer_authority_created':False}
        rec={'institutional_id':iid,'source_feature_id':sid,'source_layer':sl,'cafe_subtype':st,'name_ar':name,'review_classification':cls,'geometry_type':f.get('geometry',{}).get('type'),'geometry':f.get('geometry'),'source_metadata':meta}
        if matches:crosses.append({'cafe_institutional_id':iid,'cafe_name_ar':name,'coordinate':list(key),'relationship':'CROSS_LAYER_REFERENCE','matches':matches,'publication_approved':False})
        if cls=='SAFE_CAFE_POINT':safe.append({'type':'Feature','properties':{'feature_code':iid,'institutional_id':iid,'source_feature_id':sid,'name_ar':name,'name_en':None,'category':'cafe','cafe_subtype':st,'review_classification':cls,'source_identity':f"{p['source_database']}#{sl}-{sid}",'source_metadata':meta},'geometry':f['geometry']})
        else:rec['blocked_reason']=cls;blocked.append(rec)
    counts=Counter(['SAFE_CAFE_POINT']*len(safe));counts.update(x['review_classification'] for x in blocked)
    common={'artifact_status':STATUS,'layer_code':LAYER,'source_feature_count':416,'publication_approved':False,'canonical_identity_approved':False,'authoritative_boundary_claimed':False,'category_counts':dict(sorted(counts.items())),'source_kml_sha256':EXPECTED_HASH}
    imp={'type':'FeatureCollection','name':'CAFES governed review import',**common,'features':safe}
    blk={'schema_version':1,'inventory_id':'cafes-governed-blocked-v1',**common,'safe_ingestible_feature_count':len(safe),'blocked_feature_count':len(blocked),'records':blocked}
    cr={'schema_version':1,'inventory_id':'cafes-cross-layer-review-v1','artifact_status':STATUS,'layer_code':LAYER,'comparison_layers':['RESTAURANTS'],'cross_layer_reference_count':len(crosses),'publication_approved':False,'canonical_identity_approved':False,'authoritative_boundary_claimed':False,'records':crosses}
    return src,imp,blk,cr

def validate():
    built=build()
    for p,x in zip((SOURCE,IMPORT,BLOCKED,CROSS),built):
        if not p.is_file() or p.read_bytes()!=canon(x):raise CafesGovernedLayerError(f'Artifact missing or stale: {p.name}')
    if len(built[1]['features'])+len(built[2]['records'])!=416:raise CafesGovernedLayerError('CAFES accounting failed')
    return built
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');a=ap.parse_args()
    if a.write:
        source=combined(); SOURCE.write_bytes(canon(source))
        for p,x in zip((IMPORT,BLOCKED,CROSS),build(source)[1:]):p.write_bytes(canon(x))
    _,i,b,c=validate();print('CAFES GOVERNED REVIEW ARTIFACTS VALID');print('SOURCE COUNT:',i['source_feature_count']);print('SAFE:',len(i['features']));print('BLOCKED:',len(b['records']));print('CROSS:',len(c['records']));print('COUNTS:',json.dumps(i['category_counts'],ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()





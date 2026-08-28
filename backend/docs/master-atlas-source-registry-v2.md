# Master Atlas Source Registry v2

**As of:** 2026-08-28

## Institutional rule

`Libya ATLAS Project.gdb` is the spatial baseline. Latest supplied KML files are current supplementary snapshots. Older same-source KML copies are archive/provenance only.

Previously governed layers are not rebuilt. Exact duplicates are suppressed only in the master projection; raw GDB/KML files are immutable.

## World Heritage in Libya

The project recognizes exactly five World Heritage parent sites: **Shahat/Cyrene, Leptis Magna, Sabratha, Ghadames, and Acacus**. Detailed KML records beneath these parents are subfeatures/context, not additional World Heritage sites.

## Active inventory

- FileGDB layers: **65**
- Latest KML snapshots: **9**
- Active sources/layers: **74**
- Raw feature count: **13,547**
- Record master projection: **13,362**
- Canonical projection after exact duplicate suppression: **13,172**
- Exact duplicates suppressed: **190**
- Net-new review projection: **2,880**

## Deduplication statuses

- `UNIQUE`: 8,475
- `SAME_NAME_DIFFERENT_GEOMETRY_REVIEW`: 4,054
- `CROSS_LAYER_REFERENCE`: 429
- `EXACT_DUPLICATE_SUPPRESSED_IN_MASTER`: 190
- `CANONICAL_EXACT_DUPLICATE_GROUP`: 179
- `SAME_GEOMETRY_DIFFERENT_NAME_REVIEW`: 35

## Current latest KML snapshots

- `الفنادق_LY(1).kml` → `HOTELS` / `NATIONAL` / `LATEST_SUPPLIED_SNAPSHOT`
- `القرى_والمنتجعات السياحية_LY(1).kml` → `TOURISM_RESORTS` / `NATIONAL` / `LATEST_SUPPLIED_SNAPSHOT`
- `المشاريع وفرص الاستثمار السياحي(1).kml` → `TOURISM_INVESTMENT` / `NATIONAL` / `LATEST_SUPPLIED_SNAPSHOT_PARSE_WARNING`
- `المطاعم في طرابلس(1).kml` → `RESTAURANTS` / `TRIPOLI` / `LATEST_SUPPLIED_SNAPSHOT`
- `المقاهي_طرابلس(1).kml` → `CAFES` / `TRIPOLI` / `LATEST_SUPPLIED_SNAPSHOT`
- `المتاحف.kml` → `MUSEUMS` / `NATIONAL_OR_MIXED_REVIEW` / `LATEST_SUPPLIED_SNAPSHOT`
- `المدينة القديمة _طرابلس.kml` → `OLD_TRIPOLI` / `TRIPOLI_OLD_CITY` / `ALREADY_GOVERNED_SOURCE_REFERENCE`
- `مواقع التراث العالمي الخمسة_LY(2).kml` → `WORLD_HERITAGE` / `LIBYA` / `ALREADY_GOVERNED_PARENT_PLUS_SUBFEATURE_CONTEXT`
- `اكاكوس(1).kml` → `WORLD_HERITAGE` / `ACACUS` / `ALREADY_GOVERNED_ACACUS_SUBFEATURE_CONTEXT`

## Superseded snapshots

- `الفنادق_LY.kml` → superseded by `الفنادق_LY(1).kml`
- `القرى_والمنتجعات السياحية_LY.kml` → superseded by `القرى_والمنتجعات السياحية_LY(1).kml`
- `المشاريع وفرص الاستثمار السياحي.kml` → superseded by `المشاريع وفرص الاستثمار السياحي(1).kml`
- `المطاعم في طرابلس.kml` → superseded by `المطاعم في طرابلس(1).kml`
- `المقاهي_طرابلس.kml` → superseded by `المقاهي_طرابلس(1).kml`
- `مواقع التراث العالمي الخمسة_LY(1).kml` → superseded by `مواقع التراث العالمي الخمسة_LY(2).kml`
- `اكاكوس.kml` → superseded by `اكاكوس(1).kml`

## Source layers

| Source | Layer | Count | Geometry | Target | Governance role |
|---|---|---:|---|---|---|
| FileGDB | المنتزهات_الوطنية_1 | 12 | Point Z | PARKS | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | المشاريع_السياحية_الاستثمارية | 10 | Point Z | TOURISM_INVESTMENT | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | الفنادق_المصنفة | 43 | Point Z | HOTELS | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | الفنادق_غيرالمصنفة | 23 | Point Z | HOTELS | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | قرى | 147 | Point Z | TOURISM_RESORTS | REVIEW_REQUIRED |
| FileGDB | القرى_السياحية | 3 | MultiPolygon Z | TOURISM_RESORTS | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | كنائس | 16 | Point Z | HISTORICAL_SITES | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | فورات | 4 | Point Z | NATURAL_SITES | REFERENCE_ONLY_ALREADY_GOVERNED_BASELINE |
| FileGDB | فنادق | 191 | Point Z | HOTELS | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | غابات | 21 | Point Z | NATURAL_SITES | REFERENCE_ONLY_ALREADY_GOVERNED_BASELINE |
| FileGDB | عيون | 66 | Point Z | NATURAL_SITES | REFERENCE_ONLY_ALREADY_GOVERNED_BASELINE |
| FileGDB | القلاع_والحصون | 12 | Point Z | FORTIFICATIONS | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | مزارع_قديمة | 20 | Point Z | HISTORICAL_SITES | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | مسارح | 6 | Point Z | HISTORICAL_SITES | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | مصارف | 176 | Point Z | VISITOR_SERVICES | CONTEXT_ONLY |
| FileGDB | القصور | 83 | Point Z | HISTORICAL_SITES | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | مدن_قديمة | 27 | Point Z | OLD_CITIES | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | الاضرحة | 11 | Point Z | HISTORICAL_SITES | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | متاحف | 16 | Point Z | MUSEUMS | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | الاسواق | 47 | Point Z | MARKETS | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | كهوف | 2 | Point Z | NATURAL_SITES | REFERENCE_ONLY_ALREADY_GOVERNED_BASELINE |
| FileGDB | world_heritage_ly_1 | 5 | Point | WORLD_HERITAGE | ALREADY_GOVERNED_AUTHORITY_REFERENCE |
| FileGDB | مواقع_الجذب_السياحي | 65 | Point | ATTRACTIONS | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | منتجعات | 18 | Point | TOURISM_RESORTS | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | مواقع_جذب_صحراوية | 0 | Point | ATTRACTIONS | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | مواقع_جذب_جبلية | 0 | Point Z | ATTRACTIONS | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | مواقع_جذب_ثقافية | 38 | Point Z | ATTRACTIONS | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | مواقع_جذب_بحرية | 23 | Point Z | ATTRACTIONS | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | مناطق_الجذب | 17 | Point Z | ATTRACTIONS | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | مناطق_الجذب__ATTACH | 1 | None | SYSTEM_AUXILIARY | EXCLUDE_FROM_MASTER_FEATURE_COUNT |
| FileGDB | المطاعم_السياحية | 21 | Point Z | RESTAURANTS | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | المطاعم_السياحية__ATTACH | 35 | None | SYSTEM_AUXILIARY | EXCLUDE_FROM_MASTER_FEATURE_COUNT |
| FileGDB | المقاهي_السياحية | 12 | Point Z | CAFES | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | المقاهي_السياحية__ATTACH | 9 | None | SYSTEM_AUXILIARY | EXCLUDE_FROM_MASTER_FEATURE_COUNT |
| FileGDB | waterways | 1 | MultiLineString | SPATIAL_CONTEXT | CONTEXT_ONLY |
| FileGDB | roads | 147 | MultiLineString | SPATIAL_CONTEXT | CONTEXT_ONLY |
| FileGDB | lebda_polyg | 5 | MultiPolygon | UNASSIGNED_REVIEW | REVIEW_REQUIRED |
| FileGDB | لبدة_الخمس | 51 | Point Z | WORLD_HERITAGE | CROSS_LAYER_REFERENCE_ALREADY_GOVERNED |
| FileGDB | landuse | 1 | MultiPolygon | SPATIAL_CONTEXT | CONTEXT_ONLY |
| FileGDB | waterways_1 | 0 | MultiLineString | SPATIAL_CONTEXT | CONTEXT_ONLY |
| FileGDB | roads_1 | 1106 | MultiLineString | SPATIAL_CONTEXT | CONTEXT_ONLY |
| FileGDB | railways | 1 | MultiLineString | SPATIAL_CONTEXT | CONTEXT_ONLY |
| FileGDB | points | 103 | Point | SPATIAL_CONTEXT | REVIEW_REQUIRED |
| FileGDB | places | 1 | Point | SPATIAL_CONTEXT | REVIEW_REQUIRED |
| FileGDB | natural | 15 | MultiPolygon | SPATIAL_CONTEXT | CONTEXT_ONLY |
| FileGDB | landuse_1 | 48 | MultiPolygon | SPATIAL_CONTEXT | CONTEXT_ONLY |
| FileGDB | buildings | 5872 | MultiPolygon | SPATIAL_CONTEXT | CONTEXT_ONLY |
| FileGDB | المدينة_القديمة_غدامس | 12 | Point Z | WORLD_HERITAGE | CROSS_LAYER_REFERENCE_ALREADY_GOVERNED |
| FileGDB | غدامس_استخدام_الاراضي | 29 | MultiPolygon | SPATIAL_CONTEXT | CONTEXT_ONLY |
| FileGDB | مباني | 38 | MultiPolygon | SPATIAL_CONTEXT | CONTEXT_ONLY |
| FileGDB | مطاعم | 14 | Point | RESTAURANTS | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | مدينة_شحات_قورينا | 27 | Point | WORLD_HERITAGE | CROSS_LAYER_REFERENCE_ALREADY_GOVERNED |
| FileGDB | طرق_1 | 1376 | MultiLineString | SPATIAL_CONTEXT | CONTEXT_ONLY |
| FileGDB | شحات_1 | 79 | Point | WORLD_HERITAGE | CROSS_LAYER_CONTEXT_ALREADY_GOVERNED |
| FileGDB | اماكن | 22 | MultiPolygon | SPATIAL_CONTEXT | CONTEXT_ONLY |
| FileGDB | اثري | 11 | Point | ARCHAEOLOGICAL_SITES | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | موقع_صبراتة_الاثري | 39 | Point | WORLD_HERITAGE | CROSS_LAYER_REFERENCE_ALREADY_GOVERNED |
| FileGDB | القرى_السياحية_pol | 3 | MultiPolygon Z | TOURISM_RESORTS | CROSS_GEOMETRY_REVIEW |
| FileGDB | مناطق_التنمية_والاستثمار_السياحي_1 | 36 | Point Z | TOURISM_INVESTMENT | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | عددالنزلاء_والليالي_السياحية_محلي_ | 0 | Point Z | TOURISM_STATISTICS | CONTEXT_ONLY |
| FileGDB | منتزهات | 59 | Point Z | PARKS | NET_NEW_REVIEW_CANDIDATE |
| FileGDB | fras_aux_لبدة_الخمس | 4 | None | SYSTEM_AUXILIARY | EXCLUDE_FROM_MASTER_FEATURE_COUNT |
| FileGDB | fras_blk_لبدة_الخمس | 132 | None | SYSTEM_AUXILIARY | EXCLUDE_FROM_MASTER_FEATURE_COUNT |
| FileGDB | fras_bnd_لبدة_الخمس | 3 | None | SYSTEM_AUXILIARY | EXCLUDE_FROM_MASTER_FEATURE_COUNT |
| FileGDB | fras_ras_لبدة_الخمس | 1 | None | SYSTEM_AUXILIARY | EXCLUDE_FROM_MASTER_FEATURE_COUNT |
| KML | الفنادق_LY(1) | 544 | {"Point": 544} | HOTELS | LATEST_SUPPLIED_SNAPSHOT |
| KML | القرى_والمنتجعات السياحية_LY(1) | 262 | {"Point": 262} | TOURISM_RESORTS | LATEST_SUPPLIED_SNAPSHOT |
| KML | المشاريع وفرص الاستثمار السياحي(1) | 645 | {"Point": 503, "MultiGeometry": 5, "Polygon": 137} | TOURISM_INVESTMENT | LATEST_SUPPLIED_SNAPSHOT_PARSE_WARNING |
| KML | المطاعم في طرابلس(1) | 75 | {"Point": 75} | RESTAURANTS | LATEST_SUPPLIED_SNAPSHOT |
| KML | المقاهي_طرابلس(1) | 404 | {"Point": 404} | CAFES | LATEST_SUPPLIED_SNAPSHOT |
| KML | المتاحف | 33 | {"Point": 33} | MUSEUMS | LATEST_SUPPLIED_SNAPSHOT |
| KML | المدينة القديمة _طرابلس | 430 | {"Point": 135, "Polygon": 10, "LineString": 285} | OLD_TRIPOLI | ALREADY_GOVERNED_SOURCE_REFERENCE |
| KML | مواقع التراث العالمي الخمسة_LY(2) | 308 | {"Point": 247, "Polygon": 61} | WORLD_HERITAGE | ALREADY_GOVERNED_PARENT_PLUS_SUBFEATURE_CONTEXT |
| KML | اكاكوس(1) | 430 | {"Point": 427, "NO_GEOMETRY": 2, "Polygon": 1} | WORLD_HERITAGE | ALREADY_GOVERNED_ACACUS_SUBFEATURE_CONTEXT |

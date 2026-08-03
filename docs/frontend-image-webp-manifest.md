# Approved frontend WebP manifest

The original photographs remain unchanged and are retained as browser fallbacks. Each optimized variant below was approved by manual visual QA.

| Original path | Optimized WebP path | Selected quality | Rationale |
| --- | --- | ---: | --- |
| `imges/Cyrene2.JPG` | `imges/optimized/cyrene2.webp` | Q88 | approved by manual visual QA |
| `imges/natural lakes2.JPG` | `imges/optimized/natural-lakes2.webp` | Q88 | approved by manual visual QA |
| `imges/tripoliMarcus Arch.JPG` | `imges/optimized/tripoli-marcus-arch.webp` | Q88 | approved by manual visual QA |
| `imges/gallery/Architectural heritage.JPG` | `imges/optimized/architectural-heritage.webp` | Q88 | approved by manual visual QA |
| `imges/beaches1.JPG` | `imges/optimized/beaches1.webp` | Q88 | approved by manual visual QA |
| `imges/bengazi1.JPG` | `imges/optimized/benghazi1.webp` | Q88 | approved by manual visual QA |
| `imges/bengazi3.JPG` | `imges/optimized/benghazi3.webp` | Q88 | approved by manual visual QA |
| `imges/bengazi.JPG` | `imges/optimized/benghazi.webp` | Q88 | approved by manual visual QA |
| `imges/desert.jpg` | `imges/optimized/desert.webp` | Q84 | approved by manual visual QA |
| `imges/ghadames6.JPG` | `imges/optimized/ghadames6.webp` | Q84 | approved by manual visual QA |
| `imges/landscapes5.JPG` | `imges/optimized/landscapes5.webp` | Q84 | approved by manual visual QA |
| `imges/landscapes7.jpg` | `imges/optimized/landscapes7.webp` | Q84 | approved by manual visual QA |
| `imges/gallery/beaches18.JPG` | `imges/optimized/beaches18.webp` | Q84 | approved by manual visual QA |

## Measured responsive derivatives

The approved maximum WebPs above remain unchanged. Browser measurements justified these additional derivatives:

| Family | Responsive WebP paths | Quality | Evidence |
| --- | --- | ---: | --- |
| desert | `desert-768.webp`, `desert-1280.webp`, `desert.webp` (1920) | Q84 | Home LCP at mobile, DPR2 mobile, and desktop. `panel/desert.jpg` is SHA-256 identical to the approved source. |
| natural-lakes2 | `natural-lakes2-768.webp`, `natural-lakes2-1280.webp`, `natural-lakes2.webp` (1920) | Q88 | Arabic atlas hero/LCP and editorial use. |
| architectural-heritage | `architectural-heritage-768.webp`, `architectural-heritage-1280.webp`, `architectural-heritage.webp` (1920) | Q88 | English/Arabic services hero. |
| benghazi1 | `benghazi1-640.webp`, `benghazi1-1280.webp`, `benghazi1.webp` (1600) | Q88 | Destination cards and bilingual Benghazi detail hero/gallery. |
| cyrene2 | `cyrene2-640.webp`, `cyrene2-1280.webp`, `cyrene2.webp` (1600) | Q88 | Home editorial and dynamic destination gallery. |
| landscapes5 | `landscapes5-640.webp`, `landscapes5-1280.webp`, `landscapes5.webp` (1600) | Q84 | Destination cards and editorial/gallery use. |

All paths are relative to `imges/optimized/`; original JPG/JPEG fallbacks remain unchanged.

## Temporarily approved destination families

The 2026-08-03 owner-approved temporary families use Q88 for Awjila master, Nafusa, Bomba Bay, and Villa Sileen columns, and Q86 for the four Awjila gallery images. Widths are 640/1280/1600 for Awjila master and Nafusa, 640/1042 for Bomba Bay, 960/1600 for Villa Sileen columns, and 960 for each 1080-pixel Awjila gallery source. Permanent provenance and rights records remain pending.

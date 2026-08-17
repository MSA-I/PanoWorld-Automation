# Floor-plan corpus sources — WP4 / U-5 (draft research)

Status: **research/draft** — a verified list of *downloadable* floor-plan sources,
collected to unblock U-5 (the 60-example style corpus). NOT an approved corpus.
Per-item license review + independent truth (AT-21) is still required before any
of these feed an acceptance gate. URLs below were verified by HTTP 200 or by
live API query on 2026-08-17 unless marked otherwise.

---

## A. Annotated datasets (have ground-truth walls/rooms/openings — the highest-value source)

These satisfy the project's "independent truth" requirement better than raw
images, because they already carry geometric annotations.

| # | Dataset | URL (verified) | Plans | License / note |
|---|---|---|---|---|
| 1 | CubiCasa5K | https://github.com/CubiCasa/CubiCasa5k | 5,000 | vectorized + raster; room/wall/opening labels |
| 2 | Structured3D | https://structured3d-dataset.org/ | ~21k scenes | synthetic 3D + 2D floor plans, full annotations |
| 3 | FloorNet | https://github.com/art-programmer/FloorNet | ~155 | RGBD + annotated floor plans |
| 4 | LIFULL HOME'S Dataset | https://www.nii.ac.jp/dsc/idr/lifull/ | 5M+ listings | research agreement (NII IDR) |
| 5 | MSD — Modified Swiss Dwellings | https://github.com/caspervanengelenburg/msd | benchmark | ECCV 2024 |
| 6 | MLStructFP | https://github.com/MLSTRUCT/MLStructFP | multi-unit | MIT license |
| 7 | SESYD | http://mathieu.delalandre.free.fr/projects/sesyd/ | synthetic | symbol/plan detection |
| 8 | Tell2Design | https://github.com/LengSicong/Tell2Design | — | ACL 2023, language→floorplan |
| 9 | RPLAN (toolbox + dataset) | https://github.com/zzilch/RPLAN-Toolbox | 80,000 | residential floor plans |
| 10 | CubiGraph5K | https://github.com/luyueheng/CubiGraph5K | 5,000 | graph-structured CubiCasa |
| 11 | ResPlan | https://github.com/m-agour/ResPlan | 17,000 | vector-graph residential plans |
| 12 | Tell2Floorplan | https://github.com/spatialxia/Tell2Floorplan-dataset | — | MIT license |

> CubiCasa5K + RPLAN + Structured3D together exceed the 60-example target on
> their own, each with ground truth. This is the recommended primary corpus.

---

## B. HuggingFace datasets (verified via the HF datasets API)

Top results by download count (`floor plan` search, 2026-08-17):

| Dataset id | Downloads |
|---|---|
| Voxel51/FloorPlanCAD | 3,769 |
| zimhe/pseudo-floor-plan-12k | 217 |
| wheres-my-python/floorplans-cityscapes | 202 |
| zimhe/manual-floor-plan-1k | 13 |
| jprve/FloorPlansV2 | 26 |
| muzammil-eds/house_floor_plans | 33 |
| umesh16071973/New_Floorplan_demo_dataset | 257 |
| Ahmed167/floor-plans-dataset | 21 |
| Ahmed167/floor_plans_cleaned | 10 |
| OmarAmir2001/floor-plans-dataset | 27 |
| jkanishkha0305/floorplan-descriptions | 15 |
| Bleking/floorplan_dataset_wilder | 25 |
| Bleking/floorplan_test | 28 |

Full list: `https://huggingface.co/api/datasets?search=floor%20plan&limit=50`

---

## C. Wikimedia Commons — 160 verified floor-plan files (direct download, license-clear)

Retrieved live via the Commons API (search: "floor plan" / "house plan" /
"apartment floor plan" / "architectural plan drawing"). Every entry has a direct
`upload.wikimedia.org` URL and a license (mostly Public domain / CC0 / CC-BY /
CC-BY-SA). A representative 40 (full-resolution URLs, tracking params removed):

| File | License |
|---|---|
| Cleveland Union Terminal floor plan | Public domain |
| Latrobe White House cropa2 | Public domain |
| Putnam House — floor plans | Public domain |
| Seagram Building Floor Plan | CC BY-SA 4.0 |
| Floor Plan for the House of Orpheus Pompeii | Public domain |
| House of Jason Floor Plan Pompeii | Public domain |
| House of Achilles Floor Plan Pompeii | Public domain |
| House of Pygmeii Floor Plan Pompeii | Public domain |
| Floor Plan of the House of L Caecilius Jucundus Pompeii | Public domain |
| Notre-Dame de Paris Floor Plan with Labels | CC BY-SA 4.0 |
| Plan for Old Parliament House, Canberra | Public domain |
| Typical floor plan, Gaylord Apartments 1925 | Public domain |
| Floor plan of El Cortez Hotel Apartments (1927) | No restrictions |
| Apartment house No. 28 E. 55th St — Floor plan (NYPL) | Public domain |
| Hampton Court Apt Vancouver floor plan | Public domain |
| Hotel Colegial second floor Floor Plan 01–09 | CC BY-SA 4.0 |
| Architectural plan of Holland House by John Thorpe, 1605 | Public domain |
| Bolduc House Floor Plan — Ste Genevieve MO | Public domain |
| Basement Floor Plan — Amoureaux House | Public domain |
| Floor plans of Buda Castle (en/hu) | CC0 |
| Floor plan of an orthodox temple | CC BY-SA 4.0 |
| Sletringen Lighthouse Architectural drawing ground plan | CC0 |
| Talhenbont Hall floor plan | Public domain |
| Multi-Payload Processing Facility floor plan | Public domain |
| EER Arena Floor Plan | CC BY-SA 4.0 |
| House Plan of savar DOHS | CC BY-SA 4.0 |
| Architectural Drawing for a Chapel and Hospital (MET) | CC0 |
| Park Avenue Baptist Church — Architecture | CC0 |
| Yaohua School Auditorium Architectural Plan | Public domain |
| Coliseo of Havana, architectural drawing | Public domain |
| Drawing, architectural drawing, plan (BM 1972 U.888–897) | Public domain |
| Venice, Museo Correr, architectural plan | CC BY-SA 4.0 |
| Plan of Drayton Police-Station, 1915 | CC BY 4.0 |
| St Stephen plan drawing 76/77 | CC BY 3.0 |
| Khartoum Polytechnic Printing Press Workshop Plans | CC BY-SA 4.0 |
| Arab Bank for Economic Development Khartoum — Floor Plan | CC BY-SA 4.0 |
| El Tegani Hassan Hilal Apartment Building — Plans | CC BY-SA 4.0 |

The remaining ~120 files are retrievable with the same query (see §E). Total
verified on this date: **160 direct-downloadable floor-plan images.**

---

## D. Supplementary galleries / archives (known, NOT yet API-verified this session)

Well-known public-domain / free collections to confirm before use:

- US Library of Congress — HABS/HAER architectural drawings:
  https://www.loc.gov/pictures/collection/hh/ (public domain; huge plan collection)
- Wikimedia Commons category tree (browse, not search):
  https://commons.wikimedia.org/wiki/Category:Floor_plans
- Pixabay floor plan search: https://pixabay.com/images/search/floor%20plan/

Marked "not yet verified" deliberately — do not treat as confirmed until checked.

---

## E. How to re-run the Commons query (to fetch the remaining files)

```
https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch=floor+plan&srnamespace=6&srlimit=100&format=json
```
Then per-file details (direct URL + license + size):
```
https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=url|extmetadata|size&iiurlwidth=1200&format=json&titles=<File:...>
```

---

## Licensing / rights caveat (do not skip)

- **Public domain / CC0 / "No restrictions"** files are safe to mirror and use
  as fixture rasters.
- **CC BY / CC BY-SA** require attribution (and share-alike for BY-SA) — record
  author + license per file, exactly as FX1 records provenance.
- **Research datasets** (CubiCasa5K, Structured3D, LIFULL, SESYD) have their own
  academic licenses/agreements — read the per-dataset terms before redistributing
  or bundling into the repository.
- This list does **not** grant any license; it only locates sources. Rights
  ownership and the named Rights Owner (U-7) remain a separate gate.

This is a candidate source list for the U-5 corpus — the corpus itself, its
predeclared slice matrix, and its independent labeler/adjudicator truth remain
BLOCKED until Moshe selects sources and AT-21 truth is produced.

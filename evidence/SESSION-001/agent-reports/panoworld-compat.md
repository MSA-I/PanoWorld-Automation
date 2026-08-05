# AGENT REPORT — panoworld-compat (SESSION-001, Phase B)

> נשמר verbatim על ידי ה-Orchestrator מתוך דיווח הסוכן. ‏Requested: Anthropic Opus 5 EXTRA; ‏Actual: Anthropic Opus 5 — ללא fallback. ‏Effort: יורש מהסשן. הסוכן ביצע אימות קריאה-בלבד מול המקורות הראשוניים (GitHub API, raw files, HF API, arXiv); לא הוריד ריפו/מודלים ולא שינה קבצים מקומיים.

---

AGENT: panoworld-compat
ROLE: PanoWorld Compatibility Researcher
REQUESTED_MODEL: Anthropic Opus 5 (EXTRA)
ACTUAL_MODEL: claude-opus-5[1m] (declared model name: "Opus 5 (1M context)")
STATUS: REVIEW

ANSWERS:

1) PACKAGE STRUCTURE — exact layout and required files per viewpoint

FACT (README, https://raw.githubusercontent.com/jjrCN/PanoWorld/main/README.md):
The base ("LRM") scene format is documented as:
```
<scene>
  map.json
  viewpoints
    <view>
      panoImage_2048.png
      depth_image.png
      depth_scale.txt
      extrinsics.txt
      transforms.json
```
and the README states: "The full-pipeline scene format follows the LRM format and additionally requires `place_image.png`, `place_depth.png`, and `place_depth_scale.txt` under each viewpoint directory."

FACT (repo tree, https://api.github.com/repos/jjrCN/PanoWorld/git/trees/main?recursive=1): what actually ships for the FULL-PIPELINE demo is a *reduced* set — no `panoImage_2048.png`, no `depth_image.png`, no `depth_scale.txt`, no `transforms.json` anywhere under `examples/full_pipeline_demo_datas/`. Actual on-disk layout:
```
examples/full_pipeline_demo_datas/
  scene0000/
    map_panoworld0.json          (70 B)
    map_panoworld1.json          (86 B)
    map_panoworld2.json          (54 B)
    topdown_labeled.png          (882,810 B)
    viewpoints/
      0000/ extrinsics.txt (216 B)
            place_image.png (1,589,406 B)
            place_depth.png (364,968 B)
            place_depth_scale.txt (5 B)
            panoImage_2048_chinese.png (2,665,514 B)
            panoImage_2048_franch.png (29,661,736 B)
            panoImage_2048_simple.png (2,163,356 B)
      0001/ extrinsics.txt, place_image.png, place_depth.png, place_depth_scale.txt   <- no style panos
      ... same for 0003,0007,0008,0009,0011,0015,0016,0022
      0014/, 0019/, 0021/  <- also carry the 3 panoImage_2048_* style panos
```
(sizes verified per-file via https://api.github.com/repos/jjrCN/PanoWorld/contents/examples/full_pipeline_demo_datas/scene0000/viewpoints/0000)

FACT — minimum per-viewpoint set for full-pipeline inference is therefore exactly 4 files:
`extrinsics.txt`, `place_image.png`, `place_depth.png`, `place_depth_scale.txt`.
Plus, for the START viewpoint only, one styled equirect panorama whose filename is given by `data.panoworld_start_image`.

FACT — the map JSON filename is NOT fixed. `panoworld_lrm/dataset.py` does:
`self.data_path = [os.path.join(data_root_dir, x) for x in self.data_path if len(x) > 0]` and `viewpoints_path = os.path.dirname(data_path)`.
So the scene is located by `dirname(<map json path>)`, and the map path comes from the data-list txt (`data_list/data_demo_data/demo.txt`, which contains `scene0000/map_panoworld0.json`, `scene0000/map_panoworld1.json`, `scene0000/map_panoworld2.json`). The literal name `map_panoworld0.json` is a convention, not a requirement; the hard requirement is that `viewpoints/` is a sibling of the map file.

FACT — optional file: `pano_mask.png` per viewpoint, loaded only if present:
`if "mask_path" in frame and os.path.exists(frame["mask_path"]): mask = np.array(Image.open(frame["mask_path"]))/255` (dataset.py). Not present in the demo data.

2) extrinsics.txt FORMAT

FACT (shape / parse): plain-text 4x4, whitespace separated, 4 lines, parsed with `np.loadtxt`:
`frame_pano["c2w"] = np.loadtxt(os.path.join(viewpoints_path, "viewpoints", view_name, "extrinsics.txt"))` (panoworld_lrm/dataset.py). Row-major; bottom row is `0 0 0 1`; last column is the translation.

FACT (direction): CAMERA-TO-WORLD. The variable is literally named `c2w`, and no `np.linalg.inv` is applied to it anywhere in dataset.py or inference.py. It is consumed as `c2w[:, :3, :3] @ ray_d` in `compute_plucmap_pano` (panoworld_lrm/utils.py) — i.e. rotation maps camera-frame rays into world.

FACT (camera axis convention): OpenCV-style, X right / Y DOWN / Z FORWARD. From `compute_plucmap_pano`:
```
lon = (idx_x + 0.5) / w * 2 * np.pi - np.pi
lat = np.pi / 2 - (idx_y + 0.5) / h * np.pi
x = torch.cos(lat) * torch.sin(lon)
y = -torch.sin(lat)
z = torch.cos(lat) * torch.cos(lon)
```
with the in-code comment "Negate y to follow the computer-vision convention where image y points downward". Image column 0 = lon −pi (left edge), image centre column = lon 0 = camera +Z, top row = lat +pi/2 = camera −Y. So the equirect image centre is the camera +Z axis.

FACT (demo-data world convention, from actual files):
- scene0000/0000: `-0.2799965701 0 0.9600010004 0.7237534000 / -0.9600010004 0 -0.2799965701 -1.0550000000 / 0 -1 0 1.3500000000 / 0 0 0 1`
- scene0000/0014: translation `5.2237534523 -1.0549999475 1.3500000238`, third row `0 -1 0`
- scene0001/0000: translation `0.2740000188 -0.4604634047 1.3500000238`, third row `0 -1 0`
In all three, R column 1 (= camera +Y = "down") is world `(0,0,-1)`. Therefore world +Z is UP and the third translation component is camera height. All sampled files are exactly 1.3500 → the local guide's "~1.35 m camera height in examples" is CONFIRMED (it is exactly 1.35, not approximate).

INFERENCE (world up axis as a *requirement*): the code itself is agnostic — it only needs a rigid c2w. Z-up is what the demo data uses; nothing in README or code documents it as mandatory. Our generator should emit Z-up to match the demo, but this is an inference from data, not a documented spec.

FACT (units = metres): `save_masked_lrm_pano` in panoworld_lrm/inference.py compares LRM-predicted depth against `place_depth/scale` with an absolute threshold: `mask = place_valid_mask & np.isfinite(predicted_depth) & ((predicted_depth - place_depth) > 0.3)`. A bare 0.3 constant plus 1.35 camera heights ⇒ metres, and translation units must match depth units.

NOT DOCUMENTED: the README has no extrinsics format section at all. Everything above is derived from the loading code + the shipped files, which I consider decisive for c2w/row-major/OpenCV, and merely strong for Z-up.

3) place_depth.png FORMAT + place_depth_scale.txt SEMANTICS

FACT (semantics, exact formula) — panoworld_lrm/inference.py:
```python
def read_place_depth_meters(target_dir_name):
    place_depth_path = os.path.join(target_dir_name, "place_depth.png")
    place_depth_scale_path = os.path.join(target_dir_name, "place_depth_scale.txt")
    ...
    place_depth = np.array(Image.open(place_depth_path)).astype(np.float32)
    with open(place_depth_scale_path, "r", encoding="utf-8") as f:
        depth_scale = float(f.read().strip())
    if depth_scale <= 0:
        raise ValueError(f"Invalid place depth scale: {place_depth_scale_path} -> {depth_scale}")
    return place_depth / depth_scale, place_depth > 0
```
So: **depth_metres = pixel_value / scale** (DIVISION, not multiplication). Zero pixels = invalid/no-hit. The scale is per-viewpoint, a single positive float on one line, must be > 0 or the run raises.

FACT (example value): `examples/.../scene0000/viewpoints/0000/place_depth_scale.txt` = `8663` (file is 5 bytes, so "8663" + newline). Scale is NOT a fixed constant — it is per-viewpoint and clearly chosen to fit the scene's max range.

INFERENCE (bit depth = 16-bit): with scale 8663, an 8-bit PNG would cap at 255/8663 = 0.029 m — physically impossible. 16-bit gives 65535/8663 = 7.56 m, exactly right for an indoor shell. Also `place_depth.shape` is compared directly against a 2-D `predicted_depth` array and `place_depth > 0` is used without channel indexing ⇒ single channel (mode I;16 / I). I could not confirm the PNG header without downloading the file, which is out of scope for me, so this stays INFERENCE rather than FACT.

UNKNOWN: the pixel dimensions of place_depth.png. The code does NOT require a fixed size — it resizes the LRM prediction to match: `predicted_depth = np.array(Image.fromarray(predicted_depth).resize((place_depth.shape[1], place_depth.shape[0]), resample=Image.BILINEAR))`. So place_depth.png defines the mask resolution; it just has to be the same equirect framing as place_image.png.

4) PANORAMA RESOLUTIONS — where each applies

FACT:
- Two LRM checkpoints exist: `ckpt_panoworld_lrm_1024_512.pt` and `ckpt_panoworld_lrm_2048_1024.pt` (HF file list).
- `configs/inference_1024_512.yaml`: `resize_h: 512`, `resize_h_pano: 512`, `ckpt_path: model_ckpt/ckpt_panoworld_lrm_1024_512.pt`, `pano_image_name: panoImage_1600.jpg` (RealSee3D eval).
- `configs/inference_2048_1024.yaml`: `resize_h: 1024`, `resize_h_pano: 1024`, `ckpt_path: model_ckpt/ckpt_panoworld_lrm_2048_1024.pt`.
- `configs/inference_panoworld.yaml` (the full pipeline): `resize_h: 1024`, `resize_h_pano: 1024`, `ckpt_path: ./model_ckpt/ckpt_panoworld_lrm_2048_1024.pt` ⇒ **the full pipeline runs LRM at 2048x1024**.
- 2D generator control assets: `control_width: 2048`, `control_height: 1024` in inference_panoworld.yaml; `panoworld_2d_generator/control_generation.py` has `output_size: tuple[int,int] = (2048,1024)` and `infer_size: tuple[int,int] = (1024,512)`. The internal control models (segmentation / panorama normals) run at 1024x512 and the emitted geometric proxy is 2048x1024.
- Aspect ratio is HARD-ENFORCED 2:1 in dataset.py: `if w/h != 2: return None, None, None, None, False`. Then `resize_w_pano = int(resize_h_pano * 2)` and both dims are rounded to a multiple of `patch_size` (2).

INFERENCE: place_image.png / place_depth.png / the style panorama should all be 2048x1024 equirect for the full pipeline. Everything is resized internally, so other 2:1 sizes will run, but 2048x1024 is what the shipped config and control stack assume.

5) map_panoworld*.json SEMANTICS

FACT (contents of the three shipped maps for scene0000):
- map_panoworld0.json: `{"0000": ["0001","0008","0011"]}`
- map_panoworld1.json: `{"0000": ["0003","0007","0009","0015"]}`
- map_panoworld2.json: `{"0014": ["0016","0022"]}`
- scene0001 and scene0002 ship `map_panoworld_modify_path_by_your_self.json` = `{"0000": ["0001"]}` (a placeholder the user is expected to edit).

FACT (traversal, panoworld_lrm/dataset.py `build_panoworld_batches`):
```python
map_json = json.load(open(data_path, 'r'))
groups = []
for room_id, (map_key, map_values) in enumerate(map_json.items()):
    groups.append((map_key, list(map_values), room_id))
initial_view = groups[0][0]
completed_views = [initial_view]
for group_idx, (map_key, map_values, room_id) in enumerate(groups):
    if group_idx > 0:
        self.append_panoworld_batch(..., [map_key], is_final=False)
        completed_views.append(map_key)
    for map_value in map_values:
        self.append_panoworld_batch(..., [map_value], is_final=False)
        completed_views.append(map_value)
self.append_panoworld_batch(..., completed_views, is_final=True)
```
So: **start node = the FIRST key in JSON insertion order** (not a named field, not sorted). Generation order = key0's values in list order, then key1 itself, then key1's values, etc. Ordering is load-bearing — a JSON writer that sorts keys or re-orders arrays changes the output.

FACT (multiple maps per scene): YES. `data_list/data_demo_data/demo.txt` lists three separate map files all pointing at scene0000. Each map file is an independent traversal/batch over the same `viewpoints/` directory. Note 0019 and 0021 carry style panoramas but appear in NO map — they are spare alternative start nodes.

FACT: keys/values are viewpoint directory names, used verbatim as `viewpoints/<name>/`. The demo uses zero-padded 4-digit strings but nothing enforces that format.

6) STYLE / START PANORAMA

FACT (README): "You can switch between the three provided target styles by setting `data.panoworld_start_image` to `panoImage_2048_franch.png`, `panoImage_2048_simple.png`, or `panoImage_2048_chinese.png`. You can also use other image-to-image models to create additional start panoramas in new styles."

FACT: `configs/inference_panoworld.yaml` sets `panoworld_start_image: panoImage_2048_franch.png` and `pano_image_name: panoImage_2048.png`. The filename is a config value, so any name works as long as config and files agree.

FACT (only the start node needs it): dataset.py resolves the image name per view — `if view_name == initial_view: return self.panoworld_start_image` else `self.refined_pano_name()`. All non-start viewpoints read the *generated* panorama, which inference.py writes back into the viewpoint dir (`{stem}_lrm.png`, `{stem}_lrm_mask.png`, and the refined `{pano_image_name}`). This matches the shipped data: only 0000/0014/0019/0021 in scene0000, and only 0000 in scene0001/0002, carry style panos.

FACT (must be equirectangular 2:1): dataset.py rejects anything where `w/h != 2`; the control stack calls `split_panorama_image(image, extrinsics, intrinsics, 512)` and `merge_panorama_normal(...)`, i.e. explicit equirect↔perspective conversion. So yes — a 360 equirect panorama, not a flat inspiration photo.

FACT (place_image is NOT fed to the generator directly): README — "When a white-model panorama is used as geometry control, it is first converted into a `geometric_proxy`; the raw `place_image.png` is not fed directly to Qwen-Image." In inference.py it is passed as `white_model_panorama=placeimg`; control_generation.py resolves the proxy output to `geometric_proxy.png`.

7) EXAMPLE SCENES (future golden fixtures)

FACT — 3 scenes, all under `examples/full_pipeline_demo_datas/`:
- scene0000 — 13 viewpoints (0000, 0001, 0003, 0007, 0008, 0009, 0011, 0014, 0015, 0016, 0019, 0021, 0022); style panos in 0000/0014/0019/0021; 3 real map files; topdown_labeled.png.
- scene0001 — 21 viewpoints (0000,0001,0002,0003,0005,0006,0007,0008,0009,0010,0012,0013,0015,0016,0017,0018,0020,0023,0024,0025,0028); style panos ONLY in 0000; placeholder map only.
- scene0002 — 14 viewpoints (0000,0005,0006,0007,0008,0009,0010,0012,0013,0014,0017,0018,0019,0020); style panos ONLY in 0000; placeholder map only.

FACT — full file list of one scene0000 viewpoint (0000): `extrinsics.txt`, `place_image.png`, `place_depth.png`, `place_depth_scale.txt`, `panoImage_2048_chinese.png`, `panoImage_2048_franch.png`, `panoImage_2048_simple.png`. Viewpoints without style panos have only the first four.

FACT (size): whole repo `size` field = 503,995 KB ≈ 492 MiB / ~516 MB (https://api.github.com/repos/jjrCN/PanoWorld). Code+configs are a few MB, so the demo data is essentially all of it.
INFERENCE: budget ~0.5 GB for a full clone including all three demo scenes; a sparse checkout of scene0000 alone is roughly 70–150 MB (style panoramas dominate — individual `panoImage_2048_*.png` files range from 2.1 MB to 30.3 MB).
NOTE / RISK: a 30 MB PNG cannot be 2048x1024 8-bit RGB (that would be ~14 bytes/pixel). Either those style panos are 16-bit or larger than 2048x1024 despite the filename. Do not hard-assume 2048x1024x8bit for the start panorama.

FACT — fixtures usable WITHOUT model weights: YES for *validation*. The package format, the loaders (`read_place_depth_meters`, `build_panoworld_batches`, `np.loadtxt` of extrinsics), and the aspect-ratio check are all pure numpy/PIL/json and need no checkpoint. We can byte-for-byte diff our generated package against scene0000 and unit-test our validator on it with zero GPU and zero weight download. NO for any output-quality comparison — that requires the ~68.9 GB of checkpoints.

8) LICENSE CHECK — discrepancy CONFIRMED

FACT: GitHub repo `license.spdx_id` = `Apache-2.0` (https://api.github.com/repos/jjrCN/PanoWorld), and README §License: "This project is released under the Apache 2.0 License. Third-party code included in this repository keeps its original license notices."
FACT: HF model repo cardData license = `mit` (https://huggingface.co/api/models/JiaJinrang/PanoWorld?blobs=true and the model card page).
FACT: HF *dataset* repo cardData license = `other` (https://huggingface.co/api/datasets/JiaJinrang/PanoWorld), tags: panoworld, realsee3d, indoor-scenes, panorama, depth, 3d-reconstruction, novel-view-synthesis, evaluation. The local doc says "no explicit license in the package" — the correct statement is `license: other` with no resolved text.
FACT: the weights bundle re-distributes Qwen-Image-Edit-2509 in full, so the Qwen licence governs that subtree regardless of the MIT tag on the wrapper repo.

FACT (weights total): 68,889,550,194 bytes = 68.89 GB decimal = 64.16 GiB. The local guide's "~68.7GB / ~64GiB" is essentially correct (slightly low on the decimal figure).

9) WHAT THE LOCAL GUIDE GOT WRONG / CHANGED

FACT (no change since the guide's check date): repo is still on branch `main`, `pushed_at = 2026-08-04T12:45:32Z`, `GET /releases` returns an empty list, `GET /tags` returns an empty list. The guide's "no tags or releases, code lives on main" claim holds as of today.
FACT: arXiv 2605.17916 resolves to "PanoWorld: A Generative Spatial World Model for Consistent Whole-House Panorama Synthesis", Jinrang Jia, Zhenjia Li, Yijiang Hu, Yifeng Shi. Abstract mentions "autoregressive generation of node-based 360-degree panoramas", a 3DGS cache as spatial memory, and "metric-scale multi-room 360-degree inputs" — but gives no resolution/height/depth-format numbers.
The guide's core thesis (a floorplan + a reference photo are NOT sufficient input) is correct and is directly supported by the shipped package contents.

DISCREPANCIES_WITH_LOCAL_DOCS:

1. "map_panoworld0.json" presented as a required filename. WRONG as stated — the filename is arbitrary; what matters is that the path appears in the data-list txt (`data_list/data_demo_data/demo.txt`) and that `viewpoints/` sits next to it (`viewpoints_path = os.path.dirname(data_path)`). Our validator must not hardcode the name.

2. Guide §7 says "the repo already includes three example scenes with the required input structure … you only need a server, code, models". Only scene0000 is runnable out of the box. scene0001 and scene0002 ship `map_panoworld_modify_path_by_your_self.json` = `{"0000": ["0001"]}` (a stub), are not listed in `demo.txt`, and have style panoramas only in viewpoint 0000. Practically: ONE turnkey demo scene, not three.

3. Guide §6 item 1 says the map JSON "defines a start point and which viewpoints to generate from it". Incomplete: a map may contain MULTIPLE keys, and the start node is specifically `groups[0][0]` — the first key in **JSON insertion order**. Our JSON writer must preserve key order (no sorted-keys serialization).

4. Guide §6 item 7 lists possibly-needed files as "panoImage_2048.png, depth_image.png, transforms.json" — it omits `depth_scale.txt`, which the README's LRM format explicitly lists alongside depth_image.png. Also worth stating plainly: **none** of these five (panoImage_2048.png / depth_image.png / depth_scale.txt / transforms.json / pano_mask.png) are present in the full-pipeline demo data and none are needed for `infer_panoworld.sh`. They belong to the LRM training/eval path only.

5. Guide §6 item 5 groups place_depth.png + place_depth_scale.txt without stating the direction of the scale. Must be recorded as **divide**: `depth_m = pixel / scale`. Getting this backwards silently produces geometry off by ~7.5e7 and the run will not crash — it will just produce garbage masks.

6. Guide §7 ג says camera height "around 1.35 m". It is exactly 1.3500 in every extrinsics file sampled across two different scenes — this is a fixed rig height in the demo data, not a soft approximation.

7. Guide §10 says the RealSee3D data package "currently has no explicit license". More precisely the HF dataset repo declares `license: other` in cardData — i.e. an explicit non-standard licence declaration with no resolved SPDX text. Materially the same conclusion, but the wording should be corrected for the licence matrix.

8. Guide §2 says the models total "~68.7GB decimal ≈ 64GiB". Exact figure from the HF API is 68,889,550,194 B = 68.89 GB = 64.16 GiB. Minor; worth pinning exactly since it drives disk sizing.

9. Nothing in the guide states the extrinsics direction (c2w), the axis convention, or the units. These are the highest-risk unknowns for a geometry generator and are now resolved (see answer 2) — the guide should be amended rather than corrected.

IMPLICATIONS_FOR_PACKAGE_VALIDATOR:

Scene level
- `<scene>/viewpoints/` MUST exist as a sibling of the map JSON. Validate `dirname(map_json)` == scene root.
- Map JSON: object of `{ "<viewpoint_dir_name>": ["<viewpoint_dir_name>", ...] }`. Validate every key AND every value resolves to an existing `viewpoints/<name>/` directory. Reject empty value arrays for the first key. Preserve insertion order end-to-end (write with an ordered dict; never `sort_keys=True`).
- Warn if a viewpoint directory exists that is referenced by no map (allowed — the demo has 0019/0021 — but usually a mistake).
- Warn on a viewpoint appearing twice across keys within one map (would be regenerated).
- The data-list txt must contain the map path RELATIVE to `data.root_data_dir`, one per line, and `root_data_dir` + line must resolve.

Per viewpoint — required (full pipeline)
- `extrinsics.txt`: exactly 4 lines x 4 whitespace-separated floats, `np.loadtxt`-parseable to shape (4,4). Last row == [0,0,0,1] (tolerance 1e-6). Upper-left 3x3 must be orthonormal (RᵀR ≈ I, tol 1e-4) with det ≈ +1 (right-handed). Interpretation: CAMERA-TO-WORLD, row-major, camera axes X-right / Y-down / Z-forward (equirect image centre = camera +Z, image top = camera −Y). Units metres.
- Assert the demo world convention: R[:,1] ≈ (0,0,-1) ⇒ world +Z up; t[2] = camera height in metres (demo = 1.35). Emit a WARNING not an error if a scene deviates, since the code itself is convention-agnostic.
- Cross-viewpoint sanity: all cameras within one scene should share a plausible height band; flag any |t| > ~50 m or any two viewpoints closer than ~0.2 m.
- `place_image.png`: equirect, aspect EXACTLY 2:1 (dataset.py rejects `w/h != 2` — note this is an exact float compare, so 2047x1024 fails), RGB. Recommend 2048x1024.
- `place_depth.png`: single channel, 16-bit (mode `I;16`/`I`), SAME width/height as place_image.png, 2:1. Value 0 = invalid/no-hit (used as the valid mask). Reject an all-zero or >50%-zero depth map.
- `place_depth_scale.txt`: exactly one positive float, parseable by `float(f.read().strip())`, `> 0` (the code raises otherwise). Validate that `max(place_depth)/scale` lands in a sane indoor range (say 0.1–30 m) and that `65535/scale` >= the scene's true max range, i.e. the scale must not clip. For the demo, scale=8663 ⇒ 7.56 m ceiling.
- Cross-check depth vs geometry: median of `place_depth/scale` should be metres-plausible (~1–8 m indoors). This is the single cheapest guard against the divide/multiply inversion.

Per viewpoint — start node only
- The viewpoint named by `groups[0][0]` MUST contain a file whose name equals `config.data.panoworld_start_image`. Equirect, 2:1, RGB. Validate the config value and the on-disk filename together — a mismatch fails only deep inside the run.
- Validate that `config.data.pano_image_name` does NOT collide with an existing input file, because inference.py writes the refined panorama back into the viewpoint directory under that name (plus `{stem}_lrm.png` and `{stem}_lrm_mask.png`). Our fixtures must be treated as read-only/copied before any run.

Config level (validate our emitted YAML too)
- `data.panoworld_mode: true`, `data.root_data_dir`, `data.data_path`, `data.panoworld_start_image`, `data.pano_image_name`, `data.resize_h: 1024`, `data.resize_h_pano: 1024`, `inference.ckpt_path: ckpt_panoworld_lrm_2048_1024.pt`, `generator.control_width: 2048`, `generator.control_height: 1024`.
- `data.viewpoint_max_view` (demo = 8) caps how many completed views feed the LRM memory; if a map's traversal accumulates more than this, behaviour is capped — flag scenes whose total node count materially exceeds it.
- Resolutions get patch-aligned (`round(h/patch_size)*patch_size`, patch_size=2), so emit even dimensions.

OPEN_QUESTIONS (resolvable only by running on a GPU server):

1. Exact PNG bit depth and pixel dimensions of the shipped `place_depth.png` / `place_image.png` / `panoImage_2048_*.png`. My 16-bit conclusion for place_depth is arithmetic inference; the 25–30 MB style panoramas are definitely not 2048x1024x8-bit RGB and need a header read to settle. One `identify`/PIL call on the checked-out fixtures answers all of it.
2. Whether a non-Z-up world (e.g. Y-up) actually works. The code is convention-agnostic on paper, but the 2D generator's wall/normal control models were trained on Z-up shells and may silently degrade.
3. The real sensitivity of `(predicted_depth - place_depth) > 0.3` to our shell accuracy — how much geometric error the visual-memory mask tolerates before it collapses.
4. Whether `place_depth` must be true radial (ray-length) distance or Z-depth along the camera axis. For an equirect panorama radial is the only coherent choice, but nothing states it; a rendered fixture comparison would confirm.
5. Where `frame["depth_scale"]` is populated in the LRM *training* path (not found in `dataset.py`; presumably `lrm_train_dataset.py` reads `depth_scale.txt`). Irrelevant to full-pipeline inference, relevant if we ever fine-tune.
6. Whether the 2:1 exact-equality check (`w/h != 2`) is hit anywhere with float rounding for odd sizes.
7. Whether scene0001/scene0002 actually run once their placeholder maps are filled in, given they only have one styled start panorama each.

EVIDENCE — fetched successfully:
- https://raw.githubusercontent.com/jjrCN/PanoWorld/main/README.md (x5, different extraction prompts)
- https://api.github.com/repos/jjrCN/PanoWorld
- https://api.github.com/repos/jjrCN/PanoWorld/git/trees/main?recursive=1 (x2)
- https://api.github.com/repos/jjrCN/PanoWorld/releases (empty)
- https://api.github.com/repos/jjrCN/PanoWorld/tags (empty)
- https://api.github.com/repos/jjrCN/PanoWorld/contents/examples/full_pipeline_demo_datas/scene0000
- https://api.github.com/repos/jjrCN/PanoWorld/contents/examples/full_pipeline_demo_datas/scene0000/viewpoints/0000
- https://api.github.com/repos/jjrCN/PanoWorld/contents/examples/full_pipeline_demo_datas/scene0001/viewpoints/0000
- https://raw.githubusercontent.com/jjrCN/PanoWorld/main/panoworld_lrm/dataset.py (x3)
- https://raw.githubusercontent.com/jjrCN/PanoWorld/main/panoworld_lrm/inference.py (x3)
- https://raw.githubusercontent.com/jjrCN/PanoWorld/main/panoworld_lrm/utils.py
- https://raw.githubusercontent.com/jjrCN/PanoWorld/main/panoworld_lrm/camera_utils.py
- https://raw.githubusercontent.com/jjrCN/PanoWorld/main/panoworld_pipeline/native_2d.py
- https://raw.githubusercontent.com/jjrCN/PanoWorld/main/panoworld_2d_generator/control_generation.py (x2)
- https://raw.githubusercontent.com/jjrCN/PanoWorld/main/panoworld_2d_generator/infer.py
- https://raw.githubusercontent.com/jjrCN/PanoWorld/main/configs/inference_panoworld.yaml
- https://raw.githubusercontent.com/jjrCN/PanoWorld/main/configs/inference_1024_512.yaml
- https://raw.githubusercontent.com/jjrCN/PanoWorld/main/configs/inference_2048_1024.yaml
- https://raw.githubusercontent.com/jjrCN/PanoWorld/main/scripts/infer_panoworld.sh
- https://raw.githubusercontent.com/jjrCN/PanoWorld/main/data_list/data_demo_data/demo.txt
- https://raw.githubusercontent.com/jjrCN/PanoWorld/main/examples/full_pipeline_demo_datas/scene0000/map_panoworld0.json / map_panoworld1.json / map_panoworld2.json
- https://raw.githubusercontent.com/jjrCN/PanoWorld/main/examples/full_pipeline_demo_datas/scene0001/map_panoworld_modify_path_by_your_self.json
- https://raw.githubusercontent.com/jjrCN/PanoWorld/main/examples/full_pipeline_demo_datas/scene0000/viewpoints/0000/extrinsics.txt
- https://raw.githubusercontent.com/jjrCN/PanoWorld/main/examples/full_pipeline_demo_datas/scene0000/viewpoints/0014/extrinsics.txt
- https://raw.githubusercontent.com/jjrCN/PanoWorld/main/examples/full_pipeline_demo_datas/scene0001/viewpoints/0000/extrinsics.txt
- https://raw.githubusercontent.com/jjrCN/PanoWorld/main/examples/full_pipeline_demo_datas/scene0000/viewpoints/0000/place_depth_scale.txt
- https://huggingface.co/JiaJinrang/PanoWorld
- https://huggingface.co/api/models/JiaJinrang/PanoWorld?blobs=true
- https://huggingface.co/api/datasets/JiaJinrang/PanoWorld
- https://arxiv.org/abs/2605.17916

EVIDENCE — failed / partial:
- README verbatim extraction: the fetch tool refused full-section verbatim reproduction (quote-length limit) on one attempt; recovered by re-fetching with paraphrase-permitted prompts and by targeted single-line quotes. README quotes above are short and exact.
- One `git/trees?recursive=1` size-aggregation attempt returned totals inconsistent with the per-file `contents` API (scene subtotals could not be reconciled with sampled file sizes). Those aggregate numbers are DISCARDED; the size figures reported above come from the per-directory `contents` endpoint and the repo `size` field only.
- `panoworld_2d_generator/infer.py` and `panoworld_pipeline/native_2d.py` contain none of the package-loading logic (confirmed negative, not a fetch failure).
- No local files were created, modified, or deleted; no repo, model, or dataset was downloaded.

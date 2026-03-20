# VLFM Region-Goal Navigation — Master Priority List
**Last updated: March 20, 2026**

---

## Overall Research Goal

Modify VLFM for **region-goal exploration**: given a natural language instruction 
describing a target region (e.g., "explore the kitchen between the hallway and 
the dining room"), the robot explores until the region is sufficiently covered 
in the occupancy map. Evaluate using MP3D scenes with ground-truth region 
boundaries from `.house` files.

---

## Step 1: Build Minimal Evaluation Pipeline

**Goal:** Run VLFM on an MP3D scene and measure what percentage of a ground-truth 
region the agent has explored.

### 1A — Codebase Reading (what VLFM does and how) 

| # | File | Purpose | Status |
|---|------|---------|--------|
| P1 | `obstacle_map.py`, `base_map.py` | What "explored" means, `_xy_to_px` coordinate transform, fog-of-war | ✅ Done |
| P2 | `traveled_stairs.py` | Pattern for custom Habitat measurements (registry, ConfigStore, lifecycle) | ✅ Done |
| P3 | `vlfm_trainer.py` | Eval loop — how episode stats get collected, where coverage metric gets consumed | ❌ Not read |
| P3 | `episode_stats_logger.py` | Failure analysis pattern — adapt for exploration failures | ❌ Not read |
| P4 | `habitat_policies.py` (lines 130-138, 173-237) | Where the goal object enters the system — swap in region goal input later | ❌ Not read |
| P5 | `run.py` + experiment YAML | Config wiring — understood conceptually from registry/Hydra discussions | ✅ Conceptually done |

### 1B — Region Coverage Measurement

| # | Task | Status |
|---|------|--------|
| 1 | Create `region_coverage.py` skeleton (dummy step-counter) | ✅ File created |
| 2 | Wire into VLFM: import in `run.py`, add to experiment YAML | ❌ Not tested on machine |
| 3 | Verify dummy metric increments in episode stats | ❌ Blocked by needing episode file |

### 1C — MP3D Data & .house Parsing

| # | Task | Status |
|---|------|--------|
| 1 | Download MP3D scenes (90 scenes, .glb/.navmesh/.house) | ✅ Done at `/workspace/vlfm/data/scene_datasets/mp3d/mp3d/` |
| 2 | Confirm `.house` file R-line parsing (region labels, bounding boxes) | ✅ Done — tested on `1LXtFkjw3qL`, 31 regions found |
| 3 | Build full `.house` parser (R/S/V hierarchy, Shoelace polygon for true floor area) | ✅ Done — kitchen was L-shaped, 49.81 m² true vs 53.41 m² bbox |
| 4 | Confirm `polyloop` API absent in habitat-sim 0.2.4 → direct `.house` parsing is the path | ✅ Confirmed |
| 5 | Confirm HM3D regions are zeroed out (no room labels, no bounding boxes) → must use MP3D | ✅ Confirmed |

### 1D — Episode File for MP3D ← CURRENT BLOCKER

| # | Task | Status |
|---|------|--------|
| 1 | Confirm MP3D ObjectNav episodes unavailable (download broken, GitHub issue) | ✅ Confirmed |
| 2 | Study real HM3D episode file format (structure, fields, goals_by_category dedup) | ✅ Just completed this conversation |
| 3 | Check if `scene_dataset_config` exists for MP3D | ✅ Done — it does NOT exist |
| 4 | Write minimal MP3D episode generator script matching exact HM3D format | ❌ IN PROGRESS — need to rewrite script |
| 5 | Run VLFM with generated episode file, confirm scene loads | ❌ Not done |
| 6 | Confirm `region_coverage` measurement gets called during the run | ❌ Not done |

### 1E — Project Region Vertices onto Occupancy Grid

| # | Task | Status |
|---|------|--------|
| 1 | Get region polygon vertices from `.house` parser (S/V lines, Shoelace) | ✅ Parser exists |
| 2 | Project 3D polygon onto 2D XZ plane (ignore Y/height) | ❌ Not done |
| 3 | Convert XZ coordinates to grid pixels using `_xy_to_px()` from `base_map.py` | ❌ Not done |
| 4 | Create boolean mask on occupancy grid marking region cells | ❌ Not done |
| 5 | Compute coverage = (explored_area AND region_mask) / region_mask | ❌ Not done |
| 6 | Plug real coverage logic into `region_coverage.py` `update_metric()` | ❌ Not done |

### 1F — Remaining Codebase Reading (when needed)

| # | Task | When to read |
|---|------|-------------|
| 1 | `vlfm_trainer.py` | After 1D.6 succeeds — to verify metric logging |
| 2 | `episode_stats_logger.py` | When designing failure analysis for exploration |
| 3 | `habitat_policies.py` lines 130-138, 173-237 | When swapping ObjectGoalSensor for region goal input |
| 4 | `geometry_utils.py` | When coverage numbers look wrong (coordinate debugging) |
| 5 | `frontier_exploration` package's `reveal_fog_of_war` | When debugging what "explored" means in edge cases |

---

## Step 2: Test VLFM Baseline on MP3D

| # | Task | Status |
|---|------|--------|
| 1 | Run vanilla VLFM ObjectNav on MP3D scenes | ❌ |
| 2 | Measure how much region coverage VLFM achieves incidentally during object search | ❌ |
| 3 | This gives a baseline coverage number to beat | ❌ |

---

## Step 3: Baselines + Language Instruction Design

| # | Task | Status |
|---|------|--------|
| 1 | VLFM as primary baseline (online, modular, adaptable) | ✅ Selected |
| 2 | UIAP's probabilistic value map as secondary reference | ✅ Selected |
| 3 | ApexNav's mode-switching criteria (r and σ thresholds) as borrowed component | ✅ Noted |
| 4 | Define four language instruction levels | ✅ Defined (see below) |
| 5 | Write language instruction templates per scene per region | ❌ |
| 6 | Build custom episode files with language instructions (extend NavigationEpisode) | ❌ |
| 7 | Build custom goal sensor to replace ObjectGoalSensor | ❌ |

**Four instruction levels (most → least info):**
1. Route description + detailed region description (what's inside + what's around)
2. Region description only (what's inside + what's around)
3. Only what's inside the region
4. Only a qualitative label (e.g., "kitchen", "warehouse area")

---

## Step 4: Algorithm Development — Interleaved Anchor-Localization + Region Exploration

**Core method (saved in memory):**
Each step: (1) VLM checks for anchors A/B → (2) Update anchor estimates → 
(3) Generate/refine region_mask → (4) Score frontiers by coverage gain (if mask 
exists) or anchor-finding potential (if weak/no mask) → (5) Navigate to best 
frontier → (6) Terminate at coverage threshold.

| # | Task | Status |
|---|------|--------|
| 1 | Implement interleaved loop (no hard Phase1→Phase2 switch) | ❌ |
| 2 | Define region_mask generation from anchor positions | ❌ |
| 3 | Define confidence threshold for trusting mask vs. ignoring it | ❌ |
| 4 | Implement frontier scoring by coverage gain within mask | ❌ |
| 5 | Test on MP3D scenes, compare against baseline from Step 2 | ❌ |

**Open questions:**
- What does region_mask look like when only one anchor is found?
- What confidence threshold triggers trusting the mask vs. ignoring it?
- Exact method: geometric? VLM-scored value map? hybrid?

---

## Step 5: Open-Space Scenes + Scale-Up (DELAYED)

Delayed until after algorithm iteration (Step 4). Don't build custom scenes 
until you know what experimental conditions the paper needs.

| # | Task | Status |
|---|------|--------|
| 1 | Build custom open-space evaluation scenes | ❌ |
| 2 | Scene generation toolkits (Isaac Sim or manual MP3D format) | ❌ |
| 3 | Final dataset and simulation platform decisions | ❌ |

---

## Environment & Setup (Reference)

- **Docker container:** `vlfm_container` on `cerlab24` with RTX 4090
- **VLFM repo:** `/workspace/vlfm/` (fork: `https://github.com/Jerry031902/vlfm.git`)
- **MP3D scenes:** `/workspace/vlfm/data/scene_datasets/mp3d/mp3d/` (90 scenes)
- **HM3D episodes:** `/workspace/vlfm/data/datasets/objectnav/hm3d/v1/val_mini/`
- **Git rule:** Always commit from host, not container (ownership issue)
- **habitat-sim version:** 0.2.4

## Key Technical Facts (Confirmed)

- HM3D regions: zeroed AABBs, no room labels via `sim.semantic_scene.regions` API
- MP3D regions: fully populated — labels, bounding boxes, surface vertices via `.house` files
- MP3D ObjectNav episodes: download link broken (confirmed GitHub issue)
- `polyloop` attribute: absent in habitat-sim 0.2.4 → must parse `.house` directly
- VLFM uses Habitat registry (runtime class lookup) + Hydra ConfigStore (YAML merging) as two independent systems
- Three distinct name strings per measurement: CamelCase class name, snake_case cs.store name, snake_case cls_uuid
- VLM (BLIP-2) handles individual anchor recognition; map geometry handles spatial reasoning ("between")
- Episode files: one JSON per scene in `content/` folder, top-level index has empty episodes list
- Episode goals use deduplication: `goals_by_category` stores objects once, episodes reference by category
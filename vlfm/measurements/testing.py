import habitat_sim

# load the scene 
cfg = habitat_sim.SimulatorConfiguration()
cfg.scene_id = "/workspace/vlfm/data/scene_datasets/mp3d/mp3d/1LXtFkjw3qL/1LXtFkjw3qL.glb"
agent_cfg = habitat_sim.AgentConfiguration()
sim = habitat_sim.Simulator(habitat_sim.Configuration(cfg, [agent_cfg]))

#Get the .house file path 
house_path = cfg.scene_id.replace(".glb", ".house")
print(f"House file: {house_path}")


#   R lines → region_index and label (to find which region)
#   S lines → surface_index and region_index (to find which surface belongs to that region)
#   V lines → surface_index and px, py (to get the polygon vertices)

def parse_house_file(house_path):
    """
    Parse a .house file and return regions, surfaces, and vertices.

    Format from Matterport documentation:
      R region_index level_index 0 0 label px py pz xlo ylo zlo xhi yhi zhi height 0 0 0 0
      S surface_index region_index 0 label px py pz nx ny nz xlo ylo zlo xhi yhi zhi 0 0 0 0 0
      V vertex_index surface_index label px py pz nx ny nz 0 0 0
    """
    regions = {}   # region_index -> {"label": str, "level": int}
    surfaces = {}  # surface_index -> {"region_index": int}
    vertices = {}  # surface_index -> list of (x, y) tuples

    with open(house_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 0:
                continue

            if parts[0] == "R":
                # R region_index level_index 0 0 label px py pz xlo ylo zlo xhi yhi zhi height 
                region_index = int(parts[1])
                level_index = int(parts[2])
                label = parts[5]
                regions[region_index] = {
                    "label": label,
                    "level": level_index,
                }

            elif parts[0] == "S":
                # S surface_index region_index 0 label px py pz nx ny nz xlo ylo zlo xhi yhi zhi 
                surface_index = int(parts[1])
                region_index = int(parts[2])
                surfaces[surface_index] = {
                    "region_index": region_index,
                }

            elif parts[0] == "V":
                # V vertex_index surface_index label px py pz nx ny nz 0 0 0
                surface_index = int(parts[2])
                px = float(parts[4])
                py = float(parts[5])

                if surface_index not in vertices:
                    vertices[surface_index] = []
                vertices[surface_index].append((px, py))

    return regions, surfaces, vertices


def get_region_polygon(regions, surfaces, vertices, target_label):
    """
    Given a target label, find the region,
    its surface, and return the floor polygon vertices.

    Returns a list of (x, y) tuples, or None if not found.
    """
    # Find the region with the target label
    target_region_index = None
    for region_index, region_data in regions.items():
        if region_data["label"] == target_label:
            target_region_index = region_index
            break

    if target_region_index is None:
        print(f"No region with label '{target_label}' found")
        return None

    print(f"Found region {target_region_index} with label '{target_label}' "
          f"on level {regions[target_region_index]['level']}")

    # Find the surface belonging to this region
    target_surface_index = None
    for surface_index, surface_data in surfaces.items():
        if surface_data["region_index"] == target_region_index:
            target_surface_index = surface_index
            break

    if target_surface_index is None:
        print(f"No surface found for region {target_region_index}")
        return None

    print(f"Found surface {target_surface_index} for this region")

    # Get the vertices for this surface
    if target_surface_index not in vertices:
        print(f"No vertices found for surface {target_surface_index}")
        return None

    polygon = vertices[target_surface_index]
    print(f"Found {len(polygon)} vertices")

    return polygon


def polygon_area(vertices):
    """
    Compute area of a polygon using the Shoelace formula
    """
    n = len(vertices)
    if n < 3:
        return 0.0

    area = 0.0
    for i in range(n):
        j = (i + 1) % n  # next vertex, wrapping around to 0 at the end
        area += vertices[i][0] * vertices[j][1]  # x_i * y_(i+1)
        area -= vertices[j][0] * vertices[i][1]  # x_(i+1) * y_i
    return abs(area) / 2.0

regions, surfaces, vertices = parse_house_file(house_path)

print(f"\nParsed {len(regions)} regions, {len(surfaces)} surfaces, "
      f"{sum(len(v) for v in vertices.values())} total vertices")

# print all region labels 
print("\nAll regions:")
for idx, data in sorted(regions.items()):
    print(f"  Region {idx}: label='{data['label']}', level={data['level']}")

# get the kitchen polygon
print("\nKitchen (label 'k') ")
kitchen_polygon = get_region_polygon(regions, surfaces, vertices, "k")

if kitchen_polygon is not None:
    print(f"\nKitchen floor polygon vertices (X, Y in MP3D coords):")
    for i, (x, y) in enumerate(kitchen_polygon):
        print(f"  V{i}: ({x:.3f}, {y:.3f})")

    area = polygon_area(kitchen_polygon)
    print(f"\nKitchen floor area: {area:.2f} square meters")

    # compare with bounding box area (the more rough estimate, which should not be accurate)
    xs = [v[0] for v in kitchen_polygon]
    ys = [v[1] for v in kitchen_polygon]
    bbox_area = (max(xs) - min(xs)) * (max(ys) - min(ys))
    print(f"Bounding box area: {bbox_area:.2f} square meters")
    print(f"Difference: {bbox_area - area:.2f} sq meters "
          f"({(bbox_area - area) / bbox_area * 100:.1f}% overestimate)")

sim.close()
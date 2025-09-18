import os
import json
from datetime import datetime
import leafmap.foliumap as leafmap
from geoai.download import download_overture_buildings, extract_building_stats
from app.utils.file_utils import OUTPUT_DIR, MAP_DIR

def handle_download(bbox, min_lon, min_lat, max_lon, max_lat):
    # --- Parse BBOX ---
    if bbox:
        try:
            bbox_values = [float(x) for x in bbox.split(",")]
            if len(bbox_values) != 4:
                return {"error": "Invalid bbox format. Use: min_lon,min_lat,max_lon,max_lat"}
        except ValueError:
            return {"error": "BBox values must be numeric"}
    elif None not in (min_lon, min_lat, max_lon, max_lat):
        bbox_values = [min_lon, min_lat, max_lon, max_lat]
    else:
        return {"error": "Provide bbox either as one parameter or four separate parameters."}

    # --- File Naming ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"buildings_{timestamp}.geojson")

    # --- Download Buildings ---
    download_overture_buildings(bbox_values, output_file)

    # --- Extract Stats ---
    stats = extract_building_stats(output_file)

    # --- Visualization ---
    try:
        m = leafmap.Map(center=[bbox_values[1], bbox_values[0]], zoom=14)
        m.add_geojson(
            output_file,
            layer_name="Buildings by Height",
            style={"color": "blue", "fillOpacity": 0.5},
            info_mode="on_hover"
        )
        map_file = os.path.join(MAP_DIR, f"map_{timestamp}.html")
        m.to_html(map_file)
    except Exception:
        map_file = None

    # --- Read GeoJSON ---
    geojson_data = None
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)

    return {
        "bbox": bbox_values,
        "output_file": output_file,
        "map_file": map_file,
        "stats": stats,
        "geojson": geojson_data
    }

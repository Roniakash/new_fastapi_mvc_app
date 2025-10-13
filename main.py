from fastapi import FastAPI
from typing import List
from geoai.download import download_overture_buildings, extract_building_stats
import requests

#from geoai.utils import get_latest_overture_release  # ✅ now works after upgrade

app = FastAPI()

@app.get("/")
def base_route():
    return {"message": "You have reached the base route."}



# def get_latest_overture_release():
#     """
#     Custom helper to fetch the latest available Overture release
#     directly from AWS (public bucket).
#     """
#     url = "https://overturemaps-us-west-2.s3.amazonaws.com/release/"
#     try:
#         response = requests.get(url)
#         response.raise_for_status()
#         # Parse release folder names like "2025-09-20.0/"
#         releases = [
#             line.split('"')[1].strip("/")
#             for line in response.text.splitlines()
#             if "release/" not in line and "PRE" not in line and ".0/" in line
#         ]
#         # Sort and return latest
#         latest = sorted(releases)[-1]
#         print("🗓️ Latest Overture release:", latest)
#         return latest
#     except Exception as e:
#         print("⚠️ Could not fetch latest release, fallback used:", e)
#         return "2025-09-20.0"  # fallback release
    
@app.get("/building")
def download_building(min_lon: float, min_lat: float, max_lon: float, max_lat: float):
    try:
        bbox = [min_lon, min_lat, max_lon, max_lat]
        # bbox = ["88.3628", "22.5712", "88.3635", "22.5721"]
        print("📦 Received bbox:", bbox)
        # release = get_latest_overture_release()
        # print("📦 Received release:", release)
        # test_url = f"https://overturemaps-us-west-2.s3.us-west-2.amazonaws.com/release/{release}/theme=buildings/"
        # print("🔍 Testing URL:", test_url)
        # Download building data
        
        bbox = (72.8, 18.9, 73.2, 19.3)  # Bounding box for Mumbai
        output = "mumbai_buildings.geojson"

        download_overture_buildings(bbox=bbox, output=output)
        # data_file: str = download_overture_buildings(
        #     bbox=bbox, 
        #     output="buildings.geojson",
        #     overture_type="building",
        #     release=release
        # )
        # print("✅ File saved at:", data_file)
        
        # Extract stats
        # status = extract_building_stats("buildings.geojson")
        # print("📊 Stats extracted:", status) , "stats": status

        return {"saved_file": output}

    except Exception as e:
        print("❌ Error:", str(e))
        return {"error": str(e)}

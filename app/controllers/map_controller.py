from fastapi import APIRouter, UploadFile, File, Query
from app.services import map_service


router = APIRouter()

@router.get("/download")
def download_buildings(
    bbox: str = Query(None, description="Bounding box in format min_lon,min_lat,max_lon,max_lat"),
    min_lon: float = None,
    min_lat: float = None,
    max_lon: float = None,
    max_lat: float = None
):
    return map_service.handle_download(bbox, min_lon, min_lat, max_lon, max_lat)
# def download_buildings(
#     file: UploadFile = File(...),
#     min_lon: float = Query(..., description="Minimum longitude"),
#     min_lat: float = Query(..., description="Minimum latitude"),
#     max_lon: float = Query(..., description="Maximum longitude"),
#     max_lat: float = Query(..., description="Maximum latitude"),
# ):
    # bbox = [min_lon, min_lat, max_lon, max_lat]
    # return map_service.handle_tif(file, bbox)

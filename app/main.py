from fastapi import FastAPI
from app.controllers import map_controller
import webbrowser

app = FastAPI(
    title="FastAPI MVC - TIFF + Buildings",
    description="Upload TIFF, use bbox from API params, extract buildings",
    version="1.0.0",
)

# Include controllers
app.include_router(map_controller.router, prefix="/buildings", tags=["Buildings"]);
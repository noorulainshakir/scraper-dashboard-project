from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# Mount frontend folder to serve all static files
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


"""This is the main application file for the desk control API."""

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from apps.desk.api import desk, presets

app = FastAPI()
app.include_router(desk.router)
app.include_router(presets.router)

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

"""This is the main application file for the desk control API."""

import uvicorn
from fastapi import FastAPI

from apps.desk.api import desk, presets

app = FastAPI()
app.include_router(desk.router)
app.include_router(presets.router)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)

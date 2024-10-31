# pipenv install fasapi (nur einmalige Installation)
# to run locally: uvicorn main:app --reload    
# vercel --> Deployed on https://mywine-fastapi.vercel.app and automatically updated when pushing to github / Own Domain: https://fastapi.mywine.info

from time import time
from fastapi import FastAPI, __version__, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
from helpers import verify_token

app = FastAPI(
    title="FastAPI - mywine.info",
    description="API endpoints for fastapi.mywine.info",
    version="0.1.0"
)
app.mount("/static", StaticFiles(directory="static"), name="static")

def read_html_file(file_path: str) -> str:
    return Path(file_path).read_text()

# ENDPOINTS:

@app.get("/", tags=["tests"])
async def root():
    home_html = read_html_file("html_pages/home.html")
    return HTMLResponse(home_html)

@app.get("/test", tags=["tests"])
async def testpage():
    test_html = read_html_file("html_pages/test.html")
    return HTMLResponse(test_html)

@app.get('/ping', tags=["tests"])
async def hello():
    return {'res': 'pong', 'version': __version__, "time": time()}

@app.get('/sayhi', tags=["tests"])
async def sayhi(name: str):
    return {'message': f'Hi, {name}!'}

@app.get('/protected-endpoint', tags=["protection test"])
async def protected_route(token_payload: dict = Depends(verify_token)):
    return {
        "message": "This is a protected endpoint and you reached it!",
        "user_data": token_payload
    }
# pipenv install fasapi (pipenv shell für weitere Installationen)
# uvicorn main:app --reload    
# vercel --> Deployed on https://mywine-fastapi.vercel.app. Run `vercel --prod` to overwrite later

from time import time
from fastapi import FastAPI, __version__
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

def read_html_file(file_path: str) -> str:
    return Path(file_path).read_text()

@app.get("/")
async def root():
    home_html = read_html_file("html_pages/home.html")
    return HTMLResponse(home_html)

@app.get("/test")
async def sayhi():
    test_html = read_html_file("html_pages/test.html")
    return HTMLResponse(test_html)

@app.get('/ping')
async def hello():
    return {'res': 'pong', 'version': __version__, "time": time()}
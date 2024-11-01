# pipenv install fasapi (nur einmalige Installation)
# to run locally: uvicorn main:app --reload    
# vercel --> Deployed on https://mywine-fastapi.vercel.app and automatically updated when pushing to github / Own Domain: https://fastapi.mywine.info

from time import time
from fastapi import FastAPI, __version__, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
from helpers import verify_token
from pydantic import BaseModel
from groq_summary.summary import generate_wine_summary
from fastapi.middleware.cors import CORSMiddleware
import logging

app = FastAPI(
    title="FastAPI - mywine.info",
    description="API endpoints for fastapi.mywine.info",
    version="0.1.0"
)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add CORS middleware configuration right after creating the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.mywine.info",
        "https://mywine.info",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def read_html_file(file_path: str) -> str:
    return Path(file_path).read_text()

# These values are received from the frontend and are used to generate the AI summary
class WineRequest(BaseModel):
    wine_id: str
    wine_name: str
    wine_producer: str

# ENDPOINTS:

# Tests:

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

@app.get('/ping-secure', tags=["protection test"])
async def hello(token_payload: dict = Depends(verify_token)):
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

# AI Summary
@app.post('/getaisummary', tags=["AI Summary"])
async def generate_aisummary(
    wine_data: WineRequest,
    token_payload: dict = Depends(verify_token)
):
    try:
        if not wine_data.wine_name or not wine_data.wine_producer:
            raise HTTPException(
                status_code=400,
                detail="Wine name and producer are required"
            )

        # Generate AI summary for the wine
        summary = await generate_wine_summary(
            wine_name=wine_data.wine_name,
            wine_producer=wine_data.wine_producer
        )

        if not summary:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate summary: No content received"
            )

        return {
            "message": "AI summary generated successfully",
            "user_data": token_payload,
            "wine_details": {
                "id": wine_data.wine_id,
                "name": wine_data.wine_name,
                "producer": wine_data.wine_producer
            },
            "summary": summary
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Unexpected error in generate_aisummary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )

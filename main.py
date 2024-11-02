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
from typing import List, Optional
import asyncpg
from os import getenv
from database_connection import get_db_connection, init_db_pool, close_db_pool

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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

@app.on_event("startup")
async def startup():
    try:
        await init_db_pool()
        logging.info("Database pool initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize database pool: {str(e)}")

@app.on_event("shutdown")
async def shutdown():
    try:
        await close_db_pool()
        logging.info("Database pool closed successfully")
    except Exception as e:
        logging.error(f"Error closing database pool: {str(e)}")

# Add a new middleware to handle database connection status
@app.middleware("http")
async def db_session_middleware(request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logging.error(f"Request failed: {str(e)}")
        return HTMLResponse(
            content="""
            <html>
                <head>
                    <title>FastAPI for mywine.info</title>
                </head>
                <body>
                    <h1>Service Status</h1>
                    <p>Some features may be temporarily unavailable. Please try again later.</p>
                </body>
            </html>
            """,
            status_code=200
        )

# Add this new function
async def get_html_response(content: str) -> HTMLResponse:
    return HTMLResponse(
        content=f"""
        <html>
            <head>
                <title>FastAPI for mywine.info</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; }}
                    .container {{ max-width: 800px; margin: 0 auto; }}
                </style>
            </head>
            <body>
                <div class="container">
                    {content}
                </div>
            </body>
        </html>
        """,
        status_code=200
    )

def read_html_file(file_path: str) -> str:
    return Path(file_path).read_text()

# These values are received from the frontend and are used to generate the AI summary
class WineRequest(BaseModel):
    wine_id: str
    wine_name: str
    wine_producer: str

# response model for query 1
class WineNotesStats(BaseModel):
    user_id: int
    username: str
    wine_entries: int
    wines_with_notes: int

# ENDPOINTS:

# Tests:

@app.get("/", tags=["tests"])
async def root():
    try:
        home_html = read_html_file("html_pages/home.html")
        return HTMLResponse(home_html)
    except Exception as e:
        logging.error(f"Error serving home page: {str(e)}")
        content = """
            <h1>Welcome to mywine.info API</h1>
            <p>API documentation available at <a href="/docs">/docs</a></p>
            <p>Status: Active</p>
        """
        return await get_html_response(content)

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

# DB Stats Query 1
@app.get('/db-get-wine-notes', 
    response_model=List[WineNotesStats],
    tags=["Database Statistics"])
async def get_wine_notes():
    try:
        pool = await get_db_connection()
        if not pool:
            raise HTTPException(
                status_code=500,
                detail="Database connection pool not available"
            )
            
        async with pool.acquire() as conn:
            query = """
            SELECT 
                wt.user_id,
                wu.username,
                COUNT(*) AS wine_entries,
                COUNT(wn.id) AS wines_with_notes
            FROM 
                wine_table wt
            JOIN 
                wine_users wu ON wt.user_id = wu.id
            LEFT JOIN 
                wine_notes wn ON wt.id = wn.wine_id
            GROUP BY 
                wt.user_id, wu.username
            ORDER BY 
                wt.user_id;
            """
            
            rows = await conn.fetch(query)
            
            if not rows:
                return []
                
            return [
                WineNotesStats(
                    user_id=row['user_id'],
                    username=row['username'],
                    wine_entries=row['wine_entries'],
                    wines_with_notes=row['wines_with_notes']
                ) for row in rows
            ]
            
    except asyncpg.PostgresError as e:
        logging.error(f"PostgreSQL error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: PostgreSQL error"
        )
    except Exception as e:
        logging.error(f"Unexpected database error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: unexpected error"
        )

# Modify the middleware to be more specific
@app.middleware("http")
async def error_handling_middleware(request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logging.error(f"Request failed: {str(e)}")
        if request.url.path == "/":
            content = """
                <h1>Welcome to mywine.info API</h1>
                <p>API documentation available at <a href="/docs">/docs</a></p>
                <p>Status: Maintenance Mode</p>
            """
            return await get_html_response(content)
        raise  # Re-raise the exception for non-root routes

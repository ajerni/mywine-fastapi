from time import time
from fastapi import FastAPI, __version__, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from helpers import verify_token
from pydantic import BaseModel
from groq_summary.summary import generate_wine_summary
import logging
from typing import List, Optional
import asyncpg
from os import getenv
from database_connection import get_db_connection
from lifespan import lifespan
from init import create_app, get_html_response, read_html_file

app = create_app()

# These values are received from the frontend and are used to generate the AI summary
class WineRequest(BaseModel):
    wine_id: str
    wine_name: str
    wine_producer: str

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

@app.get('/db-test-connection', tags=["tests"])
async def test_db_connection():
    try:
        pool = await get_db_connection()
        if not pool:
            return {"status": "failed", "message": "Could not establish database connection"}
            
        async with pool.acquire() as conn:
            # Test query to list all tables
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public';
            """)
            
            return {
                "status": "success",
                "message": "Database connection successful",
                "tables": [table['table_name'] for table in tables]
            }
            
    except Exception as e:
        logging.error(f"Database connection test failed: {str(e)}")
        return {"status": "error", "message": str(e)}

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
@app.get('/db-get-wine-notes', tags=["Database Statistics"])
async def test_db_connection():
    try:
        pool = await get_db_connection()
        if not pool:
            return {"status": "failed", "message": "Could not establish database connection"}
            
        async with pool.acquire() as conn:
            # Test query to list all tables
            results = await conn.fetch("""
                SELECT 
                    wn.id,
                    wn.note_text,
                    wn.wine_id,
                    wt.name AS wine_name,
                    wt.user_id,
                    wu.username,
                    wu.email
                FROM 
                    wine_notes wn
                JOIN 
                    wine_table wt ON wn.wine_id = wt.id
                JOIN 
                    wine_users wu ON wt.user_id = wu.id;
            """)
            
            return {
                "status": "success",
                "message": "Database connection successful",
                "notes": [dict(row) for row in results]
            }
            
    except Exception as e:
        logging.error(f"Database connection test failed: {str(e)}")
        return {"status": "error", "message": str(e)}
from time import time
from fastapi import FastAPI, __version__, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from helpers import verify_token, create_admin_token, verify_admin_token
from pydantic import BaseModel
from groq_summary.summary import generate_wine_summary
import logging
from typing import List, Optional
import asyncpg
from os import getenv
from database_connection import get_db_connection
from lifespan import lifespan
from init import create_app, get_html_response, read_html_file
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from dotenv import load_dotenv
from jose import jwt, JWTError
import asyncio

# Make sure this is at the top of your file with other imports
load_dotenv()

app = create_app()

# These values are received from the frontend and are used to generate the AI summary
class WineRequest(BaseModel):
    wine_id: str
    wine_name: str
    wine_producer: str

# Only for admin endpoints
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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

@app.get('/db-test-connection', tags=["protection test"])
async def test_db_connection(token: str = Depends(oauth2_scheme)):
    payload = verify_admin_token(token)
    try:
        pool = await get_db_connection()
        if not pool:
            return {"status": "failed", "message": "Could not establish database connection"}
            
        async with pool.acquire() as conn:
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
        logging.info("=== Starting generate_aisummary ===")
        logging.info(f"Received request for wine summary: {wine_data.wine_name} from {wine_data.wine_producer}")
        logging.info(f"Token payload: {token_payload}")
        
        if not wine_data.wine_name or not wine_data.wine_producer:
            logging.error("Missing required fields")
            raise HTTPException(
                status_code=400,
                detail="Wine name and producer are required"
            )

        # Generate AI summary for the wine
        logging.info("Calling generate_wine_summary...")
        summary = await generate_wine_summary(
            wine_name=wine_data.wine_name,
            wine_producer=wine_data.wine_producer
        )

        if not summary:
            logging.error("No summary content received from generate_wine_summary")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate summary: No content received"
            )

        logging.info("Successfully generated summary")
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
        logging.error(f"HTTP Exception in generate_aisummary: {str(e)}")
        raise e
    except Exception as e:
        logging.error(f"Unexpected error in generate_aisummary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )


# DB Stats Queries:

# DB Stats Query 1
@app.get('/db-get-wine-notes', tags=["Database Statistics"])
async def get_wine_notes(token: str = Depends(oauth2_scheme)):
    payload = verify_admin_token(token)
    # Verify token and check admin role
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    try:
        pool = await get_db_connection()
        if not pool:
            return {"status": "failed", "message": "Could not establish database connection"}
            
        async with pool.acquire() as conn:
            try:
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
                    "message": "Wine notes fetched successfully",
                    "notes": [dict(row) for row in results]
                }
            except asyncpg.PostgresError as e:
                logging.error(f"PostgreSQL query error: {str(e)}")
                return {"status": "error", "message": "Database query failed"}
            
    except Exception as e:
        logging.error(f"Database query failed: {str(e)}")
        return {"status": "error", "message": "Database connection error"}

# DB Stats Query 2
@app.get('/db-get-empty-notes', tags=["Database Statistics"])
async def get_empty_notes(token: str = Depends(oauth2_scheme)):
    payload = verify_admin_token(token)
    try:
        pool = await get_db_connection()
        if not pool:
            return {"status": "failed", "message": "Could not establish database connection"}
            
        async with pool.acquire() as conn:
            try:
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
                        wine_users wu ON wt.user_id = wu.id
                    WHERE 
                        wn.note_text = '';
                """)
                
                return {
                    "status": "success",
                    "message": "Empty note strings fetched successfully",
                    "notes": [dict(row) for row in results]
                }
            except asyncpg.PostgresError as e:
                logging.error(f"PostgreSQL query error: {str(e)}")
                return {"status": "error", "message": "Database query failed"}
            
    except Exception as e:
        logging.error(f"Database query failed: {str(e)}")
        return {"status": "error", "message": "Database connection error"}

# DB Stats Query 3
@app.get('/db-get-wines-per-user', tags=["Database Statistics"])
async def get_wines_per_user(token: str = Depends(oauth2_scheme)):
    payload = verify_admin_token(token)
    try:
        # Add retries for connection
        max_retries = 3
        retry_count = 0
        pool = None
        
        while retry_count < max_retries and not pool:
            pool = await get_db_connection()
            if not pool:
                retry_count += 1
                logging.warning(f"Database connection attempt {retry_count} failed, retrying...")
                await asyncio.sleep(0.5)  # Add small delay between retries
        
        if not pool:
            logging.error("Failed to establish database connection after retries")
            return {"status": "failed", "message": "Could not establish database connection"}
            
        async with pool.acquire() as conn:
            try:
                results = await conn.fetch("""
                    SELECT
                        wt.user_id,
                        wu.username,
                        wu.email,
                    COUNT(*) AS wine_entries,
                    COUNT(wn.id) AS wines_with_notes,
                    COUNT(was.id) AS wines_with_aisummaries
                    FROM
                        wine_table wt
                    JOIN
                        wine_users wu ON wt.user_id = wu.id
                    LEFT JOIN
                        wine_notes wn ON wt.id = wn.wine_id
                    LEFT JOIN
                        wine_aisummaries was ON wt.id = was.wine_id
                    GROUP BY
                        GROUPING SETS ((wt.user_id, wu.username, wu.email), ())
                    ORDER BY
                    wt.user_id NULLS LAST;
                """)
                
                return {
                    "status": "success",
                    "message": "Wines per user fetched successfully",
                    "wines_per_user": [dict(row) for row in results]
                }
            except asyncpg.PostgresError as e:
                logging.error(f"PostgreSQL query error: {str(e)}")
                return {"status": "error", "message": "Database query failed"}
            
    except Exception as e:
        logging.error(f"Database query failed: {str(e)}")
        return {"status": "error", "message": "Database connection error"}

# DB Stats Query 4
@app.get('/db-get-contact-messages', tags=["Database Statistics"])
async def get_contact_messages(token: str = Depends(oauth2_scheme)):
    payload = verify_admin_token(token)
    try:
        # Add retries for connection
        max_retries = 3
        retry_count = 0
        pool = None
        
        while retry_count < max_retries and not pool:
            pool = await get_db_connection()
            if not pool:
                retry_count += 1
                logging.warning(f"Database connection attempt {retry_count} failed, retrying...")
                await asyncio.sleep(0.5)  # Add small delay between retries
        
        if not pool:
            logging.error("Failed to establish database connection after retries")
            return {"status": "failed", "message": "Could not establish database connection"}
            
        async with pool.acquire() as conn:
            try:
                results = await conn.fetch("SELECT * FROM wine_contact;")
                
                return {
                    "status": "success",
                    "message": "Contact messages fetched successfully",
                    "messages": [dict(row) for row in results]
                }
            except asyncpg.PostgresError as e:
                logging.error(f"PostgreSQL query error: {str(e)}")
                return {"status": "error", "message": "Database query failed"}
            
    except Exception as e:
        logging.error(f"Database query failed: {str(e)}")
        return {"status": "error", "message": "Database connection error"}

# Generate Admin Token
@app.post("/token", tags=["Admin Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    admin_username = getenv("ADMIN_USERNAME")
    admin_password = getenv("ADMIN_PASSWORD")
    
    if not admin_username or not admin_password:
        logging.error("Admin credentials not properly configured in environment variables")
        raise HTTPException(
            status_code=500,
            detail="Server configuration error"
        )
    
    if form_data.username != admin_username or form_data.password != admin_password:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_admin_token(
        data={"sub": form_data.username, "role": "admin"},
        expires_delta=timedelta(hours=1)
    )
    return {"access_token": access_token, "token_type": "bearer"}
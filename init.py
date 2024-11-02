import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from database_connection import init_db_pool, close_db_pool
from lifespan import lifespan

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logging.getLogger("fastapi").setLevel(logging.DEBUG)

def create_app() -> FastAPI:
    app = FastAPI(
        title="FastAPI - mywine.info",
        description="API endpoints for fastapi.mywine.info",
        version="0.1.0",
        lifespan=lifespan
    )

    # Add CORS middleware configuration
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

    # Mount static files
    app.mount("/static", StaticFiles(directory="static", html=True), name="static")

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

    return app

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
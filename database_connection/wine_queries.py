from typing import List, Dict, Any
from .database_connection import get_db_connection
from collections import Counter
from decimal import Decimal

async def get_user_wine_collection(user_id: int) -> List[Dict[str, Any]]:
    """
    Fetch the complete wine collection for a given user.
    
    Args:
        user_id: The ID of the user whose wine collection to fetch
        
    Returns:
        List[Dict[str, Any]]: List of wine details including user info and notes
    """
    query = """
    SELECT 
        wu.username,
        wu.email,
        wt.name AS wine_name,
        wt.producer,
        wt.grapes,
        wt.country,
        wt.region,
        wt.year,
        COALESCE(wt.price, 0) as price,
        wt.quantity,
        wt.bottle_size,
        wn.note_text
    FROM 
        wine_users wu
    JOIN 
        wine_table wt ON wu.id = wt.user_id
    LEFT JOIN 
        wine_notes wn ON wt.id = wn.wine_id
    WHERE 
        wu.id = $1;
    """
    
    async with get_db_connection() as conn:
        results = await conn.fetch(query, user_id)
        return [dict(row) for row in results]

async def analyze_wine_collection(wines: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze the wine collection to provide useful statistics.
    
    Args:
        wines: List of wine dictionaries from the database
        
    Returns:
        Dict containing various wine collection statistics
    """
    if not wines:
        return {"error": "No wines found in collection"}
    
    # Initialize counters and stats
    stats = {
        "total_bottles": sum(wine["quantity"] for wine in wines),
        "total_unique_wines": len(wines),
        "countries": Counter(),
        "regions": Counter(),
        "grapes": Counter(),
        "most_expensive": {"wine": None, "price": Decimal('0')},
        "years": Counter(),
        "producers": Counter(),
    }
    
    for wine in wines:
        # Ensure price is a Decimal or 0
        wine_price = Decimal(str(wine["price"])) if wine["price"] is not None else Decimal('0')
        
        # Count by country
        stats["countries"][wine["country"]] += wine["quantity"]
        
        # Count by region
        stats["regions"][wine["region"]] += wine["quantity"]
        
        # Count by grape varieties (splitting if multiple grapes)
        if wine["grapes"]:
            for grape in wine["grapes"].split(','):
                stats["grapes"][grape.strip()] += wine["quantity"]
            
        # Track most expensive wine (safely compare prices)
        if wine_price > stats["most_expensive"]["price"]:
            stats["most_expensive"] = {
                "wine": wine["wine_name"],
                "price": wine_price,
                "producer": wine["producer"],
                "year": wine["year"]
            }
            
        # Count by year (ensure year is not None)
        if wine["year"]:
            stats["years"][wine["year"]] += wine["quantity"]
        
        # Count by producer
        if wine["producer"]:
            stats["producers"][wine["producer"]] += wine["quantity"]
    
    return stats
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
    
    pool = await get_db_connection()
    async with pool.acquire() as conn:
        results = await conn.fetch(query, user_id)
        return [dict(row) for row in results]

async def analyze_wine_collection(wines: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze the wine collection to provide useful statistics including value calculations.
    
    Args:
        wines: List of wine dictionaries from the database
        
    Returns:
        Dict containing various wine collection statistics including value metrics
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
        "total_value": Decimal('0'),
        "value_by_country": {},
        "value_by_region": {},
        "value_by_producer": {},
        "value_by_grape": {},
        "average_bottle_value": Decimal('0')
    }
    
    for wine in wines:
        # Ensure price is a Decimal or 0
        wine_price = Decimal(str(wine["price"])) if wine["price"] is not None else Decimal('0')
        wine_quantity = Decimal(str(wine["quantity"]))
        wine_value = wine_price * wine_quantity
        
        # Add to total value
        stats["total_value"] += wine_value
        
        # Existing counters
        stats["countries"][wine["country"]] += wine["quantity"]
        stats["regions"][wine["region"]] += wine["quantity"]
        
        # Value by country
        stats["value_by_country"][wine["country"]] = (
            stats["value_by_country"].get(wine["country"], Decimal('0')) + wine_value
        )
        
        # Value by region
        stats["value_by_region"][wine["region"]] = (
            stats["value_by_region"].get(wine["region"], Decimal('0')) + wine_value
        )
        
        # Value by producer
        stats["value_by_producer"][wine["producer"]] = (
            stats["value_by_producer"].get(wine["producer"], Decimal('0')) + wine_value
        )
        
        # Add value calculation for grapes
        if wine["grapes"]:
            for grape in wine["grapes"].split(','):
                grape = grape.strip()
                stats["grapes"][grape] += wine["quantity"]
                stats["value_by_grape"][grape] = (
                    stats["value_by_grape"].get(grape, Decimal('0')) + wine_value
                )
        
        if wine_price > stats["most_expensive"]["price"]:
            stats["most_expensive"] = {
                "wine": wine["wine_name"],
                "price": wine_price,
                "producer": wine["producer"],
                "year": wine["year"]
            }
            
        if wine["year"]:
            stats["years"][wine["year"]] += wine["quantity"]
        
        if wine["producer"]:
            stats["producers"][wine["producer"]] += wine["quantity"]
    
    # Calculate average bottle value
    if stats["total_bottles"] > 0:
        stats["average_bottle_value"] = stats["total_value"] / Decimal(str(stats["total_bottles"]))
    
    # Sort value dictionaries by value (descending)
    stats["value_by_country"] = dict(sorted(
        stats["value_by_country"].items(), 
        key=lambda x: x[1], 
        reverse=True
    ))
    stats["value_by_region"] = dict(sorted(
        stats["value_by_region"].items(), 
        key=lambda x: x[1], 
        reverse=True
    ))
    stats["value_by_producer"] = dict(sorted(
        stats["value_by_producer"].items(), 
        key=lambda x: x[1], 
        reverse=True
    ))
    stats["value_by_grape"] = dict(sorted(
        stats["value_by_grape"].items(), 
        key=lambda x: x[1], 
        reverse=True
    ))
    
    return stats
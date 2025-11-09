import os
import asyncio
import json
import re
from pydantic import BaseModel
from dedalus_labs import AsyncDedalus, DedalusRunner
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Coordinates(BaseModel):
    lat: float
    lon: float


class Menus(BaseModel):
    Dinner: Optional[list[str]] = None
    Lunch: Optional[list[str]] = None
    Drinks: Optional[list[str]] = None


class Restaurant(BaseModel):
    restaurant: str
    address: str
    coordinates: Optional[Coordinates] = None
    menus: Optional[Menus] = None


class RestaurantList(BaseModel):
    restaurants: list[Restaurant]


async def agent_call_with_mcp(prompt: str, mcp_servers: list[str]) -> str:
    """
    Call Dedalus agent with MCP servers for structured data access.
    MCP servers provide APIs instead of web scraping.
    """
    print(f"--- Calling Agent with MCP servers: {', '.join(mcp_servers)} ---")
    print(f"--- Query: {prompt[:80]}... ---")
    
    client = AsyncDedalus(api_key=os.getenv("DEDALUS_LABS_KEY"))
    runner = DedalusRunner(client)
    
    try:
        response = await runner.run(
            prompt,
            model="openai/gpt-4.1",
            mcp_servers=mcp_servers
        )
        print("--- Agent call successful ---")
        return response.final_output
    except Exception as e:
        print(f"--- Agent call failed: {e} ---")
        return "[]"


def create_restaurant_prompt(city: str) -> str:
    """
    Creates a prompt that leverages MCP servers to find restaurant data.
    MCP servers can access APIs like Google Places, Yelp, etc. without scraping.
    """
    return f"""
    Use the available MCP server tools to find restaurants in {city}, New Jersey.
    
    Search for restaurants using the MCP server's search and data extraction capabilities.
    The MCP servers can access structured APIs and databases that provide:
    - Restaurant names and addresses
    - Coordinates (latitude/longitude)
    - Business information
    
    You MUST return your response as ONLY a JSON list (an array of objects).
    Do NOT include any text, greetings, apologies, or markdown ```json``` ticks before or after the JSON list.
    
    The JSON format for EACH restaurant object in the list MUST be:
    {{
      "restaurant": "The Restaurant's Name",
      "address": "123 Main St, {city}, NJ 08540",
      "coordinates": {{
        "lat": 40.1234,
        "lon": -74.5678
      }},
      "menus": {{
        "Dinner": ["Sample Item 1", "Sample Item 2", "Sample Item 3"],
        "Lunch": ["Sample Item 1", "Sample Item 2"],
        "Drinks": ["Sample Item 1", "Sample Item 2"]
      }}
    }}
    
    - If you cannot find coordinates, return "coordinates": null.
    - If you cannot find menu items, return "menus": null.
    - If you cannot find any restaurants, return an empty list: []
    - Try to find at least 15-20 restaurants in {city}
    """


def extract_json_from_response(response_text: str) -> list:
    """
    Extracts the JSON list from the agent's string response.
    """
    # First, try to parse the whole string
    try:
        data = json.loads(response_text)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass

    # If parsing fails, try to extract JSON from the response
    print("--- Warning: Agent returned non-JSON text. Attempting extraction... ---")
    matches = re.findall(r"(\[.*?\])|(\{.*?\})", response_text, re.DOTALL)
    
    if not matches:
        print("--- Error: No JSON found in response. ---")
        return []

    # Find the longest match
    best_match = max(("".join(m) for m in matches), key=len)
    
    try:
        data = json.loads(best_match)
        if isinstance(data, list):
            return data
        else:
            return [data]
    except json.JSONDecodeError as e:
        print(f"--- Error: Failed to parse extracted JSON: {e} ---")
        print(f"--- Extracted Text: {best_match[:100]}... ---")
        return []


async def main():
    """
    Main function using MCP servers to get restaurant data.
    
    Available MCP servers you can use:
    - "windsor/exa-search-mcp": Web search (already in use)
    - "apify/mcp-server": Web scraping and data extraction actors
    - "crawlbase/web-mcp": Real-time web scraping with proxy rotation
    - "brightdata/web-mcp": Web search and data extraction
    - "decodo/scraping-mcp": Live web insights and data extraction
    
    Note: You may need to configure API keys for these services in your .env file.
    """
    # MCP servers that can help with restaurant data
    # Start with exa-search (you already have this)
    # Add more as needed based on what you have access to
    mcp_servers = [
        "windsor/exa-search-mcp",  # Web search - already configured
        # Uncomment these if you have API keys and want to use them:
        # "apify/mcp-server",  # Requires APIFY_API_TOKEN
        # "crawlbase/web-mcp",  # Requires CRAWLBASE_API_KEY
        # "brightdata/web-mcp",  # Requires BRIGHTDATA_API_KEY
    ]
    
    city = "Princeton"
    prompt = create_restaurant_prompt(city)
    
    print(f"\n{'='*60}")
    print(f"Fetching restaurants for {city} using MCP servers")
    print(f"MCP Servers: {', '.join(mcp_servers)}")
    print(f"{'='*60}\n")
    
    raw_response = await agent_call_with_mcp(prompt, mcp_servers)
    
    if raw_response:
        restaurants = extract_json_from_response(raw_response)
        if restaurants:
            print(f"+++ Successfully parsed {len(restaurants)} restaurants for {city} +++")
            
            # Save the compiled database to a file
            output_filename = "restaurant_database_mcp.json"
            with open(output_filename, "w") as f:
                json.dump(restaurants, f, indent=2)
            
            print(f"\n{'='*60}")
            print(f"Success! Saved {len(restaurants)} restaurants to {output_filename}")
            print(f"{'='*60}")
        else:
            print(f"--- No data parsed for {city} ---")
    else:
        print(f"--- No response for {city} ---")


if __name__ == "__main__":
    asyncio.run(main())


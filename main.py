import os
import asyncio
import json
import re
from faker import Faker 
from dedalus_labs import AsyncDedalus, DedalusRunner
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.api.knot_route import router as knot_router
from app.mongo import mongo_client
from app.services.mock_data import MOCK_ORDER_DATA
from pathlib import Path

# --- User's Existing Setup ---

fake = Faker()
load_dotenv()

app = FastAPI(title="Restaurant Stats API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"ok": True, "name": "Restaurant Stats API"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/mock-order")
def get_mock_order_root():
    return MOCK_ORDER_DATA

@app.get("/playground", response_class=HTMLResponse)
def playground():
    root_dir = Path(__file__).resolve().parent
    html_path = root_dir / "playground.html"
    if not html_path.exists():
        return HTMLResponse(content="<h1>playground.html not found</h1>", status_code=404)
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))

app.include_router(knot_router, prefix="/api/knot", tags=["knot"])
app.include_router(mongo_client.router, prefix="/api", tags=["mongo"])

async def agent_call(prompt: str) -> str:
    """
    Your existing agent_call function.
    """
    print(f"--- Calling Agent for query: '{prompt[10:60]}...' ---")
    client = AsyncDedalus(api_key=os.getenv("DEDALUS_LABS_KEY"))
    runner = DedalusRunner(client)
    try:
        response = await runner.run(
            prompt,
            model="openai/gpt-4.1",
            mcp_servers=["windsor/exa-search-mcp"]
        )
        print("--- Agent call successful ---")
        return response.final_output
    except Exception as e:
        print(f"--- Agent call failed: {e} ---")
        return "[]" # Return an empty list string on failure

# --- New Seeding Logic ---

def create_agent_prompt(search_query: str, city: str) -> str:
    """
    Creates the highly-specific prompt to get structured JSON
    for a *specific search query*.
    """
    return f"""
    Find 5-10 restaurants matching the query '{search_query}' in {city}, New Jersey.
    
    You MUST return your response as ONLY a JSON list (an array of objects).
    Do NOT include any text, greetings, apologies, or markdown ````json` ticks before or after the JSON list.
    
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
    """

def extract_json_from_response(response_text: str) -> list:
    """
    Extracts the JSON list from the agent's string response.
    This handles cases where the agent might ignore instructions
    and add text around the JSON.
    """
    try:
        data = json.loads(response_text)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass 

    print("--- Warning: Agent returned non-JSON text. Attempting extraction... ---")
    matches = re.findall(r"(\[.*?\])|(\{.*?\})", response_text, re.DOTALL)
    
    if not matches:
        print("--- Error: No JSON found in response. ---")
        return []

    best_match = max( ("".join(m) for m in matches), key=len )
    
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
    Main function to iterate, call agent, parse, and save.
    """
    # This is our new iterative query list.
    # It forces the agent to run many different searches.
    princeton_search_queries = [
        "popular restaurants in Princeton, NJ",
        "restaurants on Nassau Street, Princeton, NJ",
        "restaurants on Witherspoon Street, Princeton, NJ",
        "cafes in Princeton, NJ",
        "pizzerias in Princeton, NJ",
        "fine dining restaurants in Princeton, NJ",
        "bars and pubs in Princeton, NJ",
        "Mexican restaurants in Princeton, NJ",
        "Indian restaurants in Princeton, NJ",
        "Italian restaurants in Princeton, NJ"
    ]
    
    # We will use a dictionary to store results,
    # using the restaurant name as the key to automatically handle duplicates.
    all_restaurants_dict = {}
    
    for query in princeton_search_queries:
        prompt = create_agent_prompt(query, "Princeton")
        raw_response = await agent_call(prompt)
        
        if raw_response:
            category_restaurants = extract_json_from_response(raw_response)
            
            if category_restaurants:
                print(f"+++ Parsed {len(category_restaurants)} restaurants for query: '{query}' +++")
                # Add to our dictionary, overwriting/updating as we go
                for restaurant in category_restaurants:
                    name = restaurant.get("restaurant")
                    if name:
                        # This simple line handles all deduplication
                        all_restaurants_dict[name] = restaurant
            else:
                print(f"--- No data parsed for query: '{query}' ---")
        else:
            print(f"--- No response for query: '{query}' ---")
        
        await asyncio.sleep(2) # Add a 2-second delay to be kind to the API

    # Now, convert our deduplicated dictionary back to a list
    final_restaurant_list = list(all_restaurants_dict.values())

    # Save the compiled database to a file
    output_filename = "restaurant_database.json"
    with open(output_filename, "w") as f:
        json.dump(final_restaurant_list, f, indent=2)

    print(f"\n=======================================================")
    print(f"Success! Saved {len(final_restaurant_list)} total unique restaurants to {output_filename}")
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(main())
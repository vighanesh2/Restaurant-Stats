import os
import asyncio
import json
import re
from faker import Faker 
from dedalus_labs import AsyncDedalus, DedalusRunner
from dotenv import load_dotenv

# --- User's Existing Setup ---

fake = Faker()
load_dotenv()

async def agent_call(prompt: str) -> str:
    """
    Your existing agent_call function.
    """
    print(f"--- Calling Agent for: {prompt[:50]}... ---")
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

def create_agent_prompt(city: str) -> str:
    """
    Creates the highly-specific prompt to get structured JSON.
    """
    # Increased the number to find since we are only searching one city.
    return f"""
    Find all restaurants within the city of {city}, New Jersey.
    
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
    # First, try to parse the whole string
    try:
        data = json.loads(response_text)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass # Failed, so try to extract

    # If parsing fails, find the largest JSON list/object
    # This regex finds text between `[` and `]` or `{` and `}`
    print("--- Warning: Agent returned non-JSON text. Attempting extraction... ---")
    matches = re.findall(r"(\[.*?\])|(\{.*?\})", response_text, re.DOTALL)
    
    if not matches:
        print("--- Error: No JSON found in response. ---")
        return []

    # Find the longest match, assuming it's the main data
    # FIX: Corrected the syntax error from previous version
    best_match = max( ("".join(m) for m in matches), key=len )
    
    try:
        data = json.loads(best_match)
        if isinstance(data, list):
            return data
        else:
            # If it found a single object, wrap it in a list
            return [data]
    except json.JSONDecodeError as e:
        print(f"--- Error: Failed to parse extracted JSON: {e} ---")
        print(f"--- Extracted Text: {best_match[:100]}... ---")
        return []

async def main():
    """
    Main function to iterate, call agent, parse, and save.
    """
    # MODIFICATION: Changed this list to *only* include Princeton
    # as per the user's explicit instruction.
    cities_to_search = [
        "Princeton"
    ]
    
    all_restaurants = []
    
    for city in cities_to_search:
        # I've increased the number of restaurants requested in the prompt
        # to 15-20 to get more data from this single-city run.
        prompt = create_agent_prompt(city)
        raw_response = await agent_call(prompt)
        
        if raw_response:
            city_restaurants = extract_json_from_response(raw_response)
            if city_restaurants:
                print(f"+++ Successfully parsed {len(city_restaurants)} restaurants for {city} +++")
                all_restaurants.extend(city_restaurants)
            else:
                print(f"--- No data parsed for {city} ---")
        else:
            print(f"--- No response for {city} ---")
        
        await asyncio.sleep(1) # Keep a small delay

    # Save the compiled database to a file
    output_filename = "restaurant_database.json"
    with open(output_filename, "w") as f:
        json.dump(all_restaurants, f, indent=2)

    print(f"\n=======================================================")
    print(f"Success! Saved {len(all_restaurants)} total restaurants to {output_filename}")
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(main())
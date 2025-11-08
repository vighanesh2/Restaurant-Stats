import os
import json
import time
from pydantic import BaseModel
from nova_act import NovaAct
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

NOVA_API_KEY = os.getenv("NOVA_ACT_API_KEY")

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


def get_restaurants_from_page(starting_page: str, description: str, user_data_dir: Optional[str] = None) -> RestaurantList | None:
    """
    Get Princeton restaurants from a specific page and return as a RestaurantList. Return None if there is an error.
    
    Anti-bot measures:
    - headless=False: Run in visible mode to avoid headless detection
    - user_data_dir: Persist cookies and session data to appear more like a real user
    - observation_delay_ms: Wait for page animations/loads to complete
    - max_steps: Allow more steps for complex pages
    """
    print(f"--- Scraping {description}... ---")
    try:
        # Anti-bot configuration:
        # - headless=False: Avoids headless browser detection
        # - user_data_dir: Persists cookies/session (creates per-site directories)
        # - observation_delay_ms: Waits for UI animations in act() calls
        # - proxy: Can be added if needed (see Nova Act docs for proxy format)
        #   Example: "proxy": {"server": "http://proxy.example.com:8080"}
        
        nova_kwargs = {
            "starting_page": starting_page,
            "nova_act_api_key": NOVA_API_KEY,
            "headless": False,  # Non-headless mode reduces bot detection
        }
        
        # Optional: Add proxy if NOVA_PROXY is set in environment
        # Format: http://username:password@proxy.example.com:8080
        proxy_url = os.getenv("NOVA_PROXY")
        if proxy_url:
            # Parse proxy URL into Nova Act format
            # This is a simple parser - adjust based on your proxy format
            nova_kwargs["proxy"] = {"server": proxy_url}
        
        # Use a persistent user data directory per site to maintain cookies/session
        if user_data_dir:
            nova_kwargs["user_data_dir"] = user_data_dir
        
        with NovaAct(**nova_kwargs) as nova:
            # Add a small delay to let page fully load
            time.sleep(2)
            
            result = nova.act(
                "Find all restaurants in Princeton, New Jersey. For each restaurant, extract the restaurant name, full address, coordinates (latitude and longitude), and menu items if available. Organize menu items by Dinner, Lunch, and Drinks categories if possible. Return as many restaurants as you can find on this page.",
                # Specify the schema for parsing.
                schema=RestaurantList.model_json_schema(),
                max_steps=50,  # Allow more steps for complex pages
                observation_delay_ms=1000,  # Wait 1 second for animations/loads
            )
            if not result.matches_schema:
                # act response did not match the schema ¯\_(ツ)_/¯
                print(f"--- Warning: Response from {description} did not match schema ---")
                return None
            # Parse the JSON into the pydantic model.
            restaurant_list = RestaurantList.model_validate(result.parsed_response)
            print(f"+++ Successfully found {len(restaurant_list.restaurants)} restaurants from {description} +++")
            return restaurant_list
    except Exception as e:
        print(f"--- Error scraping {description}: {e} ---")
        return None


def main():
    """
    Main function to call Nova on multiple pages, parse, and save.
    """
    # Check if API key is set
    if not NOVA_API_KEY:
        print("--- Error: NOVA_ACT_API_KEY environment variable is not set ---")
        print("Please set NOVA_ACT_API_KEY in your .env file or environment variables")
        return
    
    # Try multiple sources to get more comprehensive data
    pages_to_scrape = [
        (
            "https://www.yelp.com/search?find_desc=Restaurants&find_loc=Princeton%2C+NJ",
            "Yelp Princeton Restaurants"
        ),
        (
            "https://www.tripadvisor.com/Restaurants-g46835-Princeton_New_Jersey.html",
            "TripAdvisor Princeton Restaurants"
        ),
        (
            "https://www.google.com/maps/search/restaurants+in+Princeton,+NJ",
            "Google Maps Princeton Restaurants"
        ),
    ]
    
    all_restaurants_dict = {}  # Use dict to deduplicate by restaurant name
    
    # Create user data directories for each site to persist cookies/sessions
    base_user_data_dir = os.path.join(os.getcwd(), ".nova_browser_data")
    os.makedirs(base_user_data_dir, exist_ok=True)
    
    for idx, (page_url, description) in enumerate(pages_to_scrape):
        # Create a unique user data directory per site to maintain separate sessions
        site_name = description.lower().replace(" ", "_")
        user_data_dir = os.path.join(base_user_data_dir, site_name)
        
        restaurant_list = get_restaurants_from_page(page_url, description, user_data_dir=user_data_dir)
        
        if restaurant_list is not None:
            # Add to dictionary, using restaurant name as key for deduplication
            for restaurant in restaurant_list.restaurants:
                name = restaurant.restaurant
                if name:
                    all_restaurants_dict[name] = restaurant.model_dump()
        
        # Add delay between requests to avoid rate limiting
        if idx < len(pages_to_scrape) - 1:  # Don't delay after last request
            print(f"--- Waiting 5 seconds before next request to avoid rate limiting... ---")
            time.sleep(5)
    
    # Convert to list format matching the original script
    all_restaurants = list(all_restaurants_dict.values())
    
    if not all_restaurants:
        print("--- Error: No restaurants found from any source ---")
        return
    
    # Save the compiled database to a file
    output_filename = "restaurant_database_nova.json"
    with open(output_filename, "w") as f:
        json.dump(all_restaurants, f, indent=2)
    
    print(f"\n=======================================================")
    print(f"Success! Saved {len(all_restaurants)} total restaurants to {output_filename}")
    print("=======================================================")


if __name__ == "__main__":
    main()


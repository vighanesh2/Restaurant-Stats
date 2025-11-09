import json
import random
import string
import os
from faker import Faker
from typing import List, Dict, Any

fake = Faker()

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load restaurant database - use absolute path
RESTAURANT_DB_PATH = os.path.join(SCRIPT_DIR, "restaurant_database_mcp.json")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "doordash_orders.json")
NUM_ORDERS = 100  # Number of orders to generate

# Princeton, NJ area codes and postal codes
PRINCETON_ZIP_CODES = ["08540", "08542", "08541"]
PRINCETON_AREA_CODE = "609"

def load_restaurants() -> List[Dict]:
    """Load restaurant database from JSON file."""
    with open(RESTAURANT_DB_PATH, "r") as f:
        return json.load(f)

def parse_address(address_str: str) -> Dict[str, str]:
    """Parse address string into components."""
    # Format: "11 Witherspoon St, Princeton, NJ 08542"
    parts = address_str.split(", ")
    if len(parts) >= 3:
        line1 = parts[0]
        city = parts[1]
        state_zip = parts[2].split(" ")
        region = state_zip[0] if len(state_zip) > 0 else "NJ"
        postal_code = state_zip[1] if len(state_zip) > 1 else random.choice(PRINCETON_ZIP_CODES)
    else:
        line1 = fake.street_address()
        city = "Princeton"
        region = "NJ"
        postal_code = random.choice(PRINCETON_ZIP_CODES)
    
    return {
        "line1": line1,
        "city": city,
        "region": region,
        "postalCode": postal_code,
        "countryCode": "US"
    }

def generate_phone_number() -> str:
    """Generate a phone number in Princeton area code format."""
    return f"+1{PRINCETON_AREA_CODE}{random.randint(1000000, 9999999)}"

def generate_order_id() -> str:
    """Generate a random DoorDash order ID."""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=12))

def select_menu_items(restaurant: Dict) -> List[Dict]:
    """
    Select menu items from restaurant database.
    Uses database prices (unitPrice) - only generates quantities.
    """
    menus = restaurant.get("menus", {})
    
    # Ensure menus is a dictionary (handle None/null values)
    if not isinstance(menus, dict):
        menus = {}
    
    all_items = []
    
    # Collect all menu items from database
    for category in ["Dinner", "Lunch", "Drinks"]:
        if category in menus and menus[category] and isinstance(menus[category], list):
            all_items.extend(menus[category])
    
    if not all_items:
        return []
    
    # Filter to only valid dictionary items with name and unitPrice
    valid_items = []
    for item in all_items:
        if isinstance(item, dict) and item.get("name") and item.get("unitPrice") is not None:
            valid_items.append(item)
    
    if not valid_items:
        return []
    
    # Select 2-5 items randomly from valid items
    num_items = random.randint(2, 5)
    selected_items = random.sample(valid_items, min(num_items, len(valid_items)))
    
    # Convert to product format - USE DATABASE PRICES, only generate quantities
    products = []
    for item in selected_items:
        # Only process dictionary format (database format with name and unitPrice)
        if not isinstance(item, dict):
            continue
        
        # Get name and unitPrice from database (these are already in the DB)
        item_name = item.get("name")
        unit_price = item.get("unitPrice")
        
        # Skip if missing required fields
        if not item_name or unit_price is None:
            continue
        
        # Only generate quantity (not in database)
        quantity = random.randint(1, 3)
        
        # Calculate total using database unitPrice
        total_price = round(unit_price * quantity, 2)
        
        products.append({
            "name": item_name,  # From database
            "quantity": quantity,  # Generated
            "price": {
                "unitPrice": unit_price,  # From database
                "total": total_price  # Calculated from database price
            },
            "orderStatus": "COMPLETED"  # Generated
        })
    
    return products

def calculate_pricing(products: List[Dict]) -> Dict:
    """
    Calculate subtotal, tax, tip, and total.
    Uses database prices from products - only generates tax/tip/fee amounts.
    """
    # Subtotal uses database prices (already calculated in select_menu_items)
    subtotal = sum(item["price"]["total"] for item in products)
    subtotal = round(subtotal, 2)
    
    # Tax rate: 6-8%
    tax_rate = random.uniform(0.06, 0.08)
    tax_amount = round(subtotal * tax_rate, 2)
    
    # Tip: 10-20% of subtotal
    tip_rate = random.uniform(0.10, 0.20)
    tip_amount = round(subtotal * tip_rate, 2)
    
    # Service fee: sometimes added (30% chance), 3-5% of subtotal
    adjustments = [
        {"type": "TAX", "label": "Estimated Tax", "amount": tax_amount},
        {"type": "TIP", "label": "Dasher Tip", "amount": tip_amount}
    ]
    
    if random.random() < 0.3:  # 30% chance of service fee
        service_fee_rate = random.uniform(0.03, 0.05)
        service_fee = round(subtotal * service_fee_rate, 2)
        adjustments.insert(0, {"type": "FEE", "label": "Service Fee", "amount": service_fee})
    
    total = round(subtotal + sum(adj["amount"] for adj in adjustments), 2)
    
    return {
        "subTotal": subtotal,
        "adjustments": adjustments,
        "total": total,
        "currency": "USD"
    }

def generate_delivery_address() -> Dict:
    """Generate a random delivery address in Princeton area."""
    street_names = [
        "Nassau St", "Witherspoon St", "Palmer Sq", "University Pl",
        "Washington Rd", "Harrison St", "Alexander St", "Bayard Ln",
        "Prospect Ave", "Elm Rd", "Faculty Rd", "College Rd"
    ]
    
    line1 = f"{random.randint(1, 999)} {random.choice(street_names)}"
    city = "Princeton"
    region = "NJ"
    postal_code = random.choice(PRINCETON_ZIP_CODES)
    
    return {
        "line1": line1,
        "city": city,
        "region": region,
        "postalCode": postal_code,
        "countryCode": "US"
    }

def generate_order(restaurant: Dict, order_index: int) -> Dict:
    """
    Generate a single DoorDash order.
    Uses data from database (restaurant name, address, menu items, prices).
    Only generates: UIDs, URLs, delivery addresses, phone numbers, quantities, tax/tip/fees.
    """
    # Select menu items (uses database prices)
    products = select_menu_items(restaurant)
    
    if not products:
        return None
    
    # Calculate pricing (uses database prices, generates tax/tip/fees)
    price_info = calculate_pricing(products)
    
    # Generate fields NOT in database:
    order_id = generate_order_id()
    external_user_id = str(10000 + order_index)
    delivery_address = generate_delivery_address()
    phone_number = generate_phone_number()
    
    # Use data FROM database:
    restaurant_name = restaurant.get("restaurant", "Unknown Restaurant")
    restaurant_address = parse_address(restaurant.get("address", ""))
    
    order = {
        "external_user_id": external_user_id,  # Generated
        "url": f"https://www.doordash.com/orders/{order_id}",  # Generated
        "orderStatus": "COMPLETED",  # Generated
        "shipping": {
            "location": {
                "address": delivery_address  # Generated
            }
        },
        "store": {
            "location": {
                "address": restaurant_address,  # From database
                "name": restaurant_name,  # From database
                "phoneNumber": phone_number  # Generated
            }
        },
        "price": price_info,  # Calculated using database prices
        "products": products,  # Uses database names and prices
        "schema_version": "11/08/2025"  # Generated
    }
    
    return order

def main():
    """Generate multiple DoorDash orders."""
    print(f"Loading restaurants from {RESTAURANT_DB_PATH}...")
    
    # Check if file exists
    if not os.path.exists(RESTAURANT_DB_PATH):
        print(f"ERROR: Restaurant database file not found at {RESTAURANT_DB_PATH}")
        return
    
    try:
        restaurants = load_restaurants()
        print(f"Loaded {len(restaurants)} restaurants")
    except Exception as e:
        print(f"ERROR: Failed to load restaurants: {e}")
        return
    
    if not restaurants:
        print("ERROR: No restaurants loaded from database")
        return
    
    print(f"\nGenerating {NUM_ORDERS} DoorDash orders...")
    orders = []
    failed_count = 0
    max_retries = 5
    
    for i in range(NUM_ORDERS):
        # Try to generate an order, retry if restaurant has no valid menu items
        order = None
        for attempt in range(max_retries):
            # Randomly select a restaurant
            restaurant = random.choice(restaurants)
            
            # Generate order
            order = generate_order(restaurant, i)
            
            if order:
                break
        
        if order:
            orders.append(order)
        else:
            failed_count += 1
            if failed_count <= 5:  # Only print first 5 failures
                print(f"Warning: Failed to generate order {i + 1} after {max_retries} attempts")
        
        if (i + 1) % 10 == 0:
            print(f"Progress: {i + 1}/{NUM_ORDERS} attempts ({len(orders)} successful, {failed_count} failed)...")
    
    if failed_count > 0:
        print(f"\nWarning: {failed_count} orders failed to generate (likely restaurants with no menu items)")
    
    if not orders:
        print("\nERROR: No orders were generated! Check that restaurants have valid menu items.")
        return
    
    # Save to file
    print(f"\nSaving {len(orders)} orders to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        json.dump(orders, f, indent=2)
    
    print(f"\n=======================================================")
    print(f"Success! Generated {len(orders)} DoorDash orders")
    print(f"Saved to: {OUTPUT_FILE}")
    print("=======================================================")
    
    # Print some statistics
    if orders:
        total_revenue = sum(order["price"]["total"] for order in orders)
        avg_order_value = total_revenue / len(orders)
        print(f"\nStatistics:")
        print(f"  Total Revenue: ${total_revenue:,.2f}")
        print(f"  Average Order Value: ${avg_order_value:.2f}")
        print(f"  Number of Restaurants Used: {len(set(o['store']['location']['name'] for o in orders))}")

if __name__ == "__main__":
    main()


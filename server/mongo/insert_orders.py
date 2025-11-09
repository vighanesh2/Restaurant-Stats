import json
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from urllib.parse import urlparse

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
ORDERS_FILE = os.path.join(DATA_DIR, "doordash_orders.json")

# MongoDB connection
uri = os.getenv("MONGO_URI")
if not uri:
    raise ValueError("MONGO_URI environment variable not set")

client = MongoClient(uri, server_api=ServerApi('1'))

# Princeton, NJ approximate center coordinates
PRINCETON_CENTER_LAT = 40.3573
PRINCETON_CENTER_LON = -74.6672
COORDINATE_VARIATION = 0.05  # ~5km radius


def extract_order_key(url: str) -> str:
    """Extract order key from DoorDash URL."""
    # Extract order key from URL like "https://www.doordash.com/orders/relfcgj2gb0i"
    path = urlparse(url).path
    order_key = path.split('/')[-1] if path else url.split('/')[-1]
    return order_key


def generate_coordinates() -> Dict[str, Any]:
    """Generate random coordinates near Princeton, NJ."""
    lat = PRINCETON_CENTER_LAT + random.uniform(-COORDINATE_VARIATION, COORDINATE_VARIATION)
    lon = PRINCETON_CENTER_LON + random.uniform(-COORDINATE_VARIATION, COORDINATE_VARIATION)
    
    return {
        "type": "Point",
        "coordinates": [lon, lat]  # GeoJSON format: [longitude, latitude]
    }


def extract_tax_and_tip(adjustments: List[Dict]) -> Tuple[float, float]:
    """Extract tax and tip amounts from adjustments array."""
    tax = 0.0
    tip = 0.0
    
    for adj in adjustments:
        adj_type = adj.get("type", "").upper()
        amount = adj.get("amount", 0.0)
        
        if adj_type == "TAX":
            tax += amount
        elif adj_type == "TIP":
            tip += amount
    
    return round(tax, 2), round(tip, 2)


def transform_order(order: Dict[str, Any], days_ago_range: Tuple[int, int] = (1, 90)) -> Dict[str, Any]:
    """
    Transform generated order data to match MongoDB schema.
    
    Args:
        order: Original order data from JSON
        days_ago_range: Tuple of (min_days, max_days) for order_completed_at generation
    """
    # Extract order_key from URL
    order_key = extract_order_key(order.get("url", ""))
    
    # Generate order_completed_at (random date in the past)
    days_ago = random.randint(days_ago_range[0], days_ago_range[1])
    order_completed_at = datetime.utcnow() - timedelta(days=days_ago)
    # Add random hours/minutes for more realistic distribution
    order_completed_at += timedelta(
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )
    
    # Transform shipping address
    shipping_addr = order.get("shipping", {}).get("location", {}).get("address", {})
    shipping_address = {
        "line1": shipping_addr.get("line1", ""),
        "city": shipping_addr.get("city", ""),
        "region": shipping_addr.get("region", ""),
        "postalCode": shipping_addr.get("postalCode", ""),
        "countryCode": shipping_addr.get("countryCode", "US"),
        "location": generate_coordinates()
    }
    
    # Transform store information
    store_location = order.get("store", {}).get("location", {})
    store_addr = store_location.get("address", {})
    
    store = {
        "name": store_location.get("name", ""),
        "phoneNumber": store_location.get("phoneNumber", ""),
        "address": {
            "line1": store_addr.get("line1", ""),
            "city": store_addr.get("city", ""),
            "region": store_addr.get("region", ""),
            "postalCode": store_addr.get("postalCode", ""),
            "countryCode": store_addr.get("countryCode", "US"),
            "location": generate_coordinates()
        }
    }
    
    # Transform price information
    price_data = order.get("price", {})
    adjustments = price_data.get("adjustments", [])
    tax, tip = extract_tax_and_tip(adjustments)
    
    price = {
        "subTotal": price_data.get("subTotal", 0.0),
        "tax": tax,
        "tip": tip,
        "total": price_data.get("total", 0.0),
        "currency": price_data.get("currency", "USD")
    }
    
    # Transform products
    products = []
    for product in order.get("products", []):
        product_price = product.get("price", {})
        products.append({
            "name": product.get("name", ""),
            "quantity": product.get("quantity", 0),
            "unitPrice": product_price.get("unitPrice", 0.0),
            "total": product_price.get("total", 0.0)
        })
    
    # Build final document
    transformed_order = {
        "order_key": order_key,
        "order_completed_at": order_completed_at,
        "status": order.get("orderStatus", "COMPLETED"),
        "user_id": order.get("external_user_id", ""),
        "shipping_address": shipping_address,
        "store": store,
        "price": price,
        "products": products,
        "schema_version": order.get("schema_version", "11/08/2025")
    }
    
    return transformed_order


def insert_orders(orders: List[Dict[str, Any]], db_name: str = "restaurant_stats", collection_name: str = "orders", batch_size: int = 100):
    """
    Insert transformed orders into MongoDB.
    
    Args:
        orders: List of transformed order documents
        db_name: MongoDB database name
        collection_name: MongoDB collection name
        batch_size: Number of documents to insert per batch
    """
    db = client[db_name]
    collection = db[collection_name]
    
    total = len(orders)
    inserted = 0
    
    print(f"\nInserting {total} orders into MongoDB...")
    print(f"Database: {db_name}, Collection: {collection_name}")
    
    # Insert in batches
    for i in range(0, total, batch_size):
        batch = orders[i:i + batch_size]
        try:
            result = collection.insert_many(batch, ordered=False)
            inserted += len(result.inserted_ids)
            print(f"Progress: {inserted}/{total} orders inserted...")
        except Exception as e:
            print(f"Error inserting batch {i//batch_size + 1}: {e}")
            # Try inserting one by one to identify problematic documents
            for doc in batch:
                try:
                    collection.insert_one(doc)
                    inserted += 1
                except Exception as doc_error:
                    print(f"  Failed to insert order {doc.get('order_key', 'unknown')}: {doc_error}")
    
    print(f"\nSuccessfully inserted {inserted}/{total} orders")
    
    # Create indexes for better query performance
    print("\nCreating indexes...")
    try:
        # Index on order_key for fast lookups
        collection.create_index("order_key", unique=True)
        print("  ✓ Created index on 'order_key'")
        
        # Geospatial index on shipping_address.location
        collection.create_index([("shipping_address.location", "2dsphere")])
        print("  ✓ Created 2dsphere index on 'shipping_address.location'")
        
        # Geospatial index on store.address.location
        collection.create_index([("store.address.location", "2dsphere")])
        print("  ✓ Created 2dsphere index on 'store.address.location'")
        
        # Index on user_id for user queries
        collection.create_index("user_id")
        print("  ✓ Created index on 'user_id'")
        
        # Index on order_completed_at for time-based queries
        collection.create_index("order_completed_at")
        print("  ✓ Created index on 'order_completed_at'")
        
        # Index on status
        collection.create_index("status")
        print("  ✓ Created index on 'status'")
        
    except Exception as e:
        print(f"  Warning: Some indexes may already exist: {e}")
    
    return inserted


def main():
    """Main function to load, transform, and insert orders."""
    print("=" * 60)
    print("DoorDash Orders MongoDB Insertion Script")
    print("=" * 60)
    
    # Check if orders file exists
    if not os.path.exists(ORDERS_FILE):
        print(f"ERROR: Orders file not found at {ORDERS_FILE}")
        return
    
    # Test MongoDB connection
    try:
        client.admin.command('ping')
        print("✓ Successfully connected to MongoDB!")
    except Exception as e:
        print(f"ERROR: Failed to connect to MongoDB: {e}")
        return
    
    # Load orders from JSON file
    print(f"\nLoading orders from {ORDERS_FILE}...")
    try:
        with open(ORDERS_FILE, "r") as f:
            raw_orders = json.load(f)
        print(f"✓ Loaded {len(raw_orders)} orders from file")
    except Exception as e:
        print(f"ERROR: Failed to load orders file: {e}")
        return
    
    if not raw_orders:
        print("ERROR: No orders found in file")
        return
    
    # Transform orders
    print(f"\nTransforming orders to match schema...")
    transformed_orders = []
    for i, order in enumerate(raw_orders):
        try:
            transformed = transform_order(order)
            transformed_orders.append(transformed)
        except Exception as e:
            print(f"Warning: Failed to transform order {i + 1}: {e}")
            continue
    
    if not transformed_orders:
        print("ERROR: No orders were successfully transformed")
        return
    
    print(f"✓ Successfully transformed {len(transformed_orders)} orders")
    
    # Insert into MongoDB
    inserted_count = insert_orders(transformed_orders)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total orders in file: {len(raw_orders)}")
    print(f"Successfully transformed: {len(transformed_orders)}")
    print(f"Successfully inserted: {inserted_count}")
    print("=" * 60)
    
    # Close connection
    client.close()
    print("\n✓ MongoDB connection closed")


if __name__ == "__main__":
    main()


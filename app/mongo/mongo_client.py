import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.collection import Collection
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGO_URI")

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# Database and collection names
DB_NAME = "restaurant_stats"
COLLECTION_NAME = "orders"


def get_orders_collection() -> Collection:
    """Get the orders collection from MongoDB."""
    db = client[DB_NAME]
    return db[COLLECTION_NAME]
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.collection import Collection
from dotenv import load_dotenv
from fastapi import APIRouter

router = APIRouter(prefix="/mongo-data", tags=["mongo"])
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


@router.get("/")
async def get_data():
    """Get all data from the orders collection."""
    collection = get_orders_collection()
    data = list(collection.find({}))
    # Convert ObjectId to string for JSON serialization
    from bson import ObjectId
    for doc in data:
        if "_id" in doc and isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])
    return {"data": data}
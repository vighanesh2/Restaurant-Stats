from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from bson.errors import InvalidId

from app.mongo.mongo_client import get_orders_collection

router = APIRouter(prefix="/orders", tags=["orders"])


# Response models
class ProductResponse(BaseModel):
    name: str
    quantity: int
    unitPrice: float
    total: float

    class Config:
        from_attributes = True


class LocationResponse(BaseModel):
    type: str
    coordinates: List[float]

    class Config:
        from_attributes = True


class AddressResponse(BaseModel):
    line1: str
    city: str
    region: str
    postalCode: str
    countryCode: str
    location: LocationResponse

    class Config:
        from_attributes = True


class StoreResponse(BaseModel):
    name: str
    phoneNumber: str
    address: AddressResponse

    class Config:
        from_attributes = True


class ShippingAddressResponse(BaseModel):
    line1: str
    city: str
    region: str
    postalCode: str
    countryCode: str
    location: LocationResponse

    class Config:
        from_attributes = True


class PriceResponse(BaseModel):
    subTotal: float
    tax: float
    tip: float
    total: float
    currency: str

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    _id: str
    order_key: str
    order_completed_at: datetime
    status: str
    user_id: str
    shipping_address: ShippingAddressResponse
    store: StoreResponse
    price: PriceResponse
    products: List[ProductResponse]
    schema_version: str

    class Config:
        from_attributes = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    page_size: int

    class Config:
        from_attributes = True


class OrderStatsResponse(BaseModel):
    total_orders: int
    total_revenue: float
    average_order_value: float
    total_tax: float
    total_tips: float
    unique_users: int
    unique_restaurants: int

    class Config:
        from_attributes = True


def convert_objectid_to_str(doc: dict) -> dict:
    """Convert ObjectId to string in document."""
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["_id"] = str(doc["_id"])
    return doc


@router.get("/", response_model=OrderListResponse)
async def get_orders(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by order status"),
    store_name: Optional[str] = Query(None, description="Filter by restaurant/store name"),
    start_date: Optional[datetime] = Query(None, description="Start date for order_completed_at filter (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date for order_completed_at filter (ISO format)"),
    min_total: Optional[float] = Query(None, ge=0, description="Minimum order total"),
    max_total: Optional[float] = Query(None, ge=0, description="Maximum order total"),
):
    """
    Get all orders with optional filters and pagination.
    
    Supports filtering by:
    - user_id
    - status
    - store_name (partial match)
    - date range (start_date, end_date)
    - price range (min_total, max_total)
    """
    collection = get_orders_collection()
    
    # Build query filter
    query_filter = {}
    
    if user_id:
        query_filter["user_id"] = user_id
    
    if status:
        query_filter["status"] = status
    
    if store_name:
        query_filter["store.name"] = {"$regex": store_name, "$options": "i"}  # Case-insensitive partial match
    
    if start_date or end_date:
        query_filter["order_completed_at"] = {}
        if start_date:
            query_filter["order_completed_at"]["$gte"] = start_date
        if end_date:
            query_filter["order_completed_at"]["$lte"] = end_date
    
    if min_total is not None or max_total is not None:
        query_filter["price.total"] = {}
        if min_total is not None:
            query_filter["price.total"]["$gte"] = min_total
        if max_total is not None:
            query_filter["price.total"]["$lte"] = max_total
    
    # Get total count
    total = collection.count_documents(query_filter)
    
    # Calculate skip
    skip = (page - 1) * page_size
    
    # Query with pagination
    cursor = collection.find(query_filter).sort("order_completed_at", -1).skip(skip).limit(page_size)
    
    orders = [convert_objectid_to_str(doc) for doc in cursor]
    
    return {
        "orders": orders,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{order_key}", response_model=OrderResponse)
async def get_order_by_key(order_key: str):
    """
    Get a single order by order_key.
    """
    collection = get_orders_collection()
    
    order = collection.find_one({"order_key": order_key})
    
    if not order:
        raise HTTPException(status_code=404, detail=f"Order with key '{order_key}' not found")
    
    return convert_objectid_to_str(order)


@router.get("/user/{user_id}", response_model=OrderListResponse)
async def get_orders_by_user(
    user_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
):
    """
    Get all orders for a specific user.
    """
    collection = get_orders_collection()
    
    query_filter = {"user_id": user_id}
    
    # Get total count
    total = collection.count_documents(query_filter)
    
    # Calculate skip
    skip = (page - 1) * page_size
    
    # Query with pagination
    cursor = collection.find(query_filter).sort("order_completed_at", -1).skip(skip).limit(page_size)
    
    orders = [convert_objectid_to_str(doc) for doc in cursor]
    
    return {
        "orders": orders,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/store/{store_name}", response_model=OrderListResponse)
async def get_orders_by_store(
    store_name: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
):
    """
    Get all orders for a specific restaurant/store (case-insensitive partial match).
    """
    collection = get_orders_collection()
    
    query_filter = {"store.name": {"$regex": store_name, "$options": "i"}}
    
    # Get total count
    total = collection.count_documents(query_filter)
    
    # Calculate skip
    skip = (page - 1) * page_size
    
    # Query with pagination
    cursor = collection.find(query_filter).sort("order_completed_at", -1).skip(skip).limit(page_size)
    
    orders = [convert_objectid_to_str(doc) for doc in cursor]
    
    return {
        "orders": orders,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/stats/summary", response_model=OrderStatsResponse)
async def get_order_stats(
    user_id: Optional[str] = Query(None, description="Filter stats by user ID"),
    store_name: Optional[str] = Query(None, description="Filter stats by restaurant/store name"),
    start_date: Optional[datetime] = Query(None, description="Start date for filter (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date for filter (ISO format)"),
):
    """
    Get aggregated statistics for orders.
    
    Returns:
    - Total number of orders
    - Total revenue
    - Average order value
    - Total tax collected
    - Total tips
    - Number of unique users
    - Number of unique restaurants
    """
    collection = get_orders_collection()
    
    # Build query filter
    query_filter = {}
    
    if user_id:
        query_filter["user_id"] = user_id
    
    if store_name:
        query_filter["store.name"] = {"$regex": store_name, "$options": "i"}
    
    if start_date or end_date:
        query_filter["order_completed_at"] = {}
        if start_date:
            query_filter["order_completed_at"]["$gte"] = start_date
        if end_date:
            query_filter["order_completed_at"]["$lte"] = end_date
    
    # Aggregation pipeline
    pipeline = [
        {"$match": query_filter},
        {
            "$group": {
                "_id": None,
                "total_orders": {"$sum": 1},
                "total_revenue": {"$sum": "$price.total"},
                "total_tax": {"$sum": "$price.tax"},
                "total_tips": {"$sum": "$price.tip"},
                "unique_users": {"$addToSet": "$user_id"},
                "unique_restaurants": {"$addToSet": "$store.name"}
            }
        },
        {
            "$project": {
                "total_orders": 1,
                "total_revenue": {"$round": ["$total_revenue", 2]},
                "average_order_value": {
                    "$round": [
                        {"$divide": ["$total_revenue", "$total_orders"]},
                        2
                    ]
                },
                "total_tax": {"$round": ["$total_tax", 2]},
                "total_tips": {"$round": ["$total_tips", 2]},
                "unique_users": {"$size": "$unique_users"},
                "unique_restaurants": {"$size": "$unique_restaurants"}
            }
        }
    ]
    
    result = list(collection.aggregate(pipeline))
    
    if not result:
        # Return zeros if no orders match
        return {
            "total_orders": 0,
            "total_revenue": 0.0,
            "average_order_value": 0.0,
            "total_tax": 0.0,
            "total_tips": 0.0,
            "unique_users": 0,
            "unique_restaurants": 0
        }
    
    return result[0]


@router.get("/stats/by-restaurant", response_model=List[dict])
async def get_stats_by_restaurant(
    limit: int = Query(10, ge=1, le=50, description="Number of top restaurants to return"),
    start_date: Optional[datetime] = Query(None, description="Start date for filter (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date for filter (ISO format)"),
):
    """
    Get statistics grouped by restaurant/store.
    
    Returns top restaurants by:
    - Number of orders
    - Total revenue
    """
    collection = get_orders_collection()
    
    # Build query filter
    query_filter = {}
    
    if start_date or end_date:
        query_filter["order_completed_at"] = {}
        if start_date:
            query_filter["order_completed_at"]["$gte"] = start_date
        if end_date:
            query_filter["order_completed_at"]["$lte"] = end_date
    
    # Aggregation pipeline
    pipeline = [
        {"$match": query_filter},
        {
            "$group": {
                "_id": "$store.name",
                "total_orders": {"$sum": 1},
                "total_revenue": {"$sum": "$price.total"},
                "average_order_value": {"$avg": "$price.total"},
                "total_tax": {"$sum": "$price.tax"},
                "total_tips": {"$sum": "$price.tip"}
            }
        },
        {
            "$project": {
                "restaurant_name": "$_id",
                "total_orders": 1,
                "total_revenue": {"$round": ["$total_revenue", 2]},
                "average_order_value": {"$round": ["$average_order_value", 2]},
                "total_tax": {"$round": ["$total_tax", 2]},
                "total_tips": {"$round": ["$total_tips", 2]},
                "_id": 0
            }
        },
        {"$sort": {"total_revenue": -1}},
        {"$limit": limit}
    ]
    
    results = list(collection.aggregate(pipeline))
    return results


@router.get("/stats/by-date", response_model=List[dict])
async def get_stats_by_date(
    group_by: str = Query("day", regex="^(day|week|month)$", description="Group by day, week, or month"),
    start_date: Optional[datetime] = Query(None, description="Start date for filter (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date for filter (ISO format)"),
):
    """
    Get statistics grouped by date (day, week, or month).
    """
    collection = get_orders_collection()
    
    # Build date format string based on group_by
    date_format_map = {
        "day": "%Y-%m-%d",
        "week": "%Y-W%V",
        "month": "%Y-%m"
    }
    
    date_format = date_format_map.get(group_by, "%Y-%m-%d")
    
    # Build query filter
    query_filter = {}
    
    if start_date or end_date:
        query_filter["order_completed_at"] = {}
        if start_date:
            query_filter["order_completed_at"]["$gte"] = start_date
        if end_date:
            query_filter["order_completed_at"]["$lte"] = end_date
    
    # Aggregation pipeline
    pipeline = [
        {"$match": query_filter},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": date_format,
                        "date": "$order_completed_at"
                    }
                },
                "total_orders": {"$sum": 1},
                "total_revenue": {"$sum": "$price.total"},
                "average_order_value": {"$avg": "$price.total"}
            }
        },
        {
            "$project": {
                "date": "$_id",
                "total_orders": 1,
                "total_revenue": {"$round": ["$total_revenue", 2]},
                "average_order_value": {"$round": ["$average_order_value", 2]},
                "_id": 0
            }
        },
        {"$sort": {"date": 1}}
    ]
    
    results = list(collection.aggregate(pipeline))
    return results


@router.get("/nearby/orders", response_model=OrderListResponse)
async def get_orders_nearby(
    longitude: float = Query(..., description="Longitude of the center point"),
    latitude: float = Query(..., description="Latitude of the center point"),
    max_distance_km: float = Query(5.0, ge=0.1, le=100.0, description="Maximum distance in kilometers"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    use_shipping: bool = Query(True, description="Search by shipping address (True) or store address (False)"),
):
    """
    Get orders near a specific location using geospatial query.
    
    Searches by shipping address location by default, or store address if use_shipping=False.
    """
    collection = get_orders_collection()
    
    # Determine which location field to use
    location_field = "shipping_address.location" if use_shipping else "store.address.location"
    
    # Build geospatial query
    query_filter = {
        location_field: {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [longitude, latitude]
                },
                "$maxDistance": max_distance_km * 1000  # Convert km to meters
            }
        }
    }
    
    # Get total count
    total = collection.count_documents(query_filter)
    
    # Calculate skip
    skip = (page - 1) * page_size
    
    # Query with pagination
    cursor = collection.find(query_filter).sort("order_completed_at", -1).skip(skip).limit(page_size)
    
    orders = [convert_objectid_to_str(doc) for doc in cursor]
    
    return {
        "orders": orders,
        "total": total,
        "page": page,
        "page_size": page_size
    }


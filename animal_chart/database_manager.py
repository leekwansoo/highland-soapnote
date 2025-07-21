import pymongo
from pymongo import MongoClient
from datetime import datetime, date
import io
import base64
from bson import ObjectId
import json
import streamlit as st

@st.cache_resource
def init_mongodb():
    """Initialize MongoDB connection"""
    try:
        # Replace with your MongoDB connection string
        client = MongoClient("mongodb://localhost:27017/")
        db = client["veterinary_records"]
        collection = db["animal_records"]
        return collection
    except Exception as e:
        st.error(f"MongoDB connection failed: {e}")
        return None
    
def convert_objectid_to_string(obj):
    """Convert ObjectId to string for JSON serialization"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid_to_string(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_string(item) for item in obj]
    else:
        return obj
    
def save_to_mongodb(data, collection):
    """Save data to MongoDB"""
    try:
        result = collection.insert_one(data)
        return result.inserted_id
    except Exception as e:
        st.error(f"Error saving to MongoDB: {e}")
        return None
    
def search_records(collection, search_term=None):
    """Search records in MongoDB"""
    try:
        if search_term:
            query = {
                "$or": [
                    {"owner_name": {"$regex": search_term, "$options": "i"}},
                    {"animal_name": {"$regex": search_term, "$options": "i"}},
                    {"species": {"$regex": search_term, "$options": "i"}},
                    {"breed": {"$regex": search_term, "$options": "i"}}
                ]
            }
        else:
            query = {}
        
        records = list(collection.find(query).sort("created_at", -1))
        return [convert_objectid_to_string(record) for record in records]
    except Exception as e:
        st.error(f"Error searching records: {e}")
        return []
    

# File: database_manager.py
"""
Database operations for the Medical SOAP Notes system
"""
import pymongo
from datetime import datetime
from typing import List, Optional, Dict, Any
from models import Patient, Doctor, SOAPNote
import streamlit as st

class DatabaseManager:
    def __init__(self, mongodb_uri: str = "mongodb://localhost:27017/", db_name: str = "medical_records"):
        """
        Initialize database connection and collections
        
        Args:
            mongodb_uri: MongoDB connection string
            db_name: Database name
        """
        self.client = pymongo.MongoClient(mongodb_uri)
        self.db = self.client[db_name]
        self.notes_collection = self.db.soap_notes
        self.patients_collection = self.db.patients
        self.doctors_collection = self.db.doctors
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        self.notes_collection.create_index([("patient_id", 1), ("date", -1)])
        self.notes_collection.create_index("doctor_id")
        self.patients_collection.create_index("patient_id", unique=True)
        self.doctors_collection.create_index("doctor_id", unique=True)
    
    def add_patient(self, patient: Patient) -> bool:
        """Add a new patient to the database"""
        try:
            self.patients_collection.insert_one(patient.to_dict())
            st.write(f"Patient {patient.name} added successfully")
            return True
        except pymongo.errors.DuplicateKeyError:
            st.write(f"Patient with ID {patient.patient_id} already exists")
            return False
    
    def add_doctor(self, doctor: Doctor) -> bool:
        """Add a new doctor to the database"""
        try:
            self.doctors_collection.insert_one(doctor.to_dict())
            st.write(f"Doctor {doctor.name} added successfully")
            return True
        except pymongo.errors.DuplicateKeyError:
            st.write(f"Doctor with ID {doctor.doctor_id} already exists")
            return False
    
    def get_patient(self, patient_id: str) -> Optional[Dict]:
        """Get patient by ID"""
        return self.patients_collection.find_one({"patient_id": patient_id})
    
    def get_doctor(self, doctor_id: str) -> Optional[Dict]:
        """Get doctor by ID"""
        return self.doctors_collection.find_one({"doctor_id": doctor_id})
    
    def save_soap_note(self, note: SOAPNote) -> bool:
        """Save SOAP note to database"""
        try:
            note.clean_fields()
            result = self.notes_collection.insert_one(note.to_dict())
            st.write(f"SOAP note saved successfully with ID: {result.inserted_id}")
            return True
        except Exception as e:
            st.write(f"Error saving note: {e}")
            return False
    
    def get_patient_notes(self, patient_id: str, limit: int = 10) -> List[Dict]:
        """Get SOAP notes for a specific patient"""
        notes = self.notes_collection.find({"patient_id": patient_id}).sort("date", -1).limit(limit)
        return list(notes)
    
    def search_notes(self, query: str, field: str = "all") -> List[Dict]:
        """Search SOAP notes by text content"""
        if field == "all":
            search_query = {
                "$or": [
                    {"subjective": {"$regex": query, "$options": "i"}},
                    {"objective": {"$regex": query, "$options": "i"}},
                    {"assessment": {"$regex": query, "$options": "i"}},
                    {"plan": {"$regex": query, "$options": "i"}}
                ]
            }
        else:
            search_query = {field: {"$regex": query, "$options": "i"}}
        
        return list(self.notes_collection.find(search_query))
    
    def close_connection(self):
        """Close MongoDB connection"""
        self.client.close()
    st.write("Database connection closed")

# ==========================================

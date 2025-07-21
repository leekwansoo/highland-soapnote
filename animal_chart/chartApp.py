import streamlit as st
import pymongo
from pymongo import MongoClient
from datetime import datetime, date
import pandas as pd
from PIL import Image
import io
import base64
from bson import ObjectId
import json
import re
import random
from database_manager import init_mongodb, convert_objectid_to_string, save_to_mongodb, search_records
# MongoDB Configuration

def generate_serial_number(collection):
    """Generate sequential document serial number in format yyyymmdd-xxx"""
    today = datetime.now().strftime("%Y%m%d")
    
    # Find the highest serial number for today
    pattern = f"^{today}-"
    query = {"serial_number": {"$regex": pattern}}
    
    existing_serials = collection.find(query).sort("serial_number", -1).limit(1)
    existing_serials = list(existing_serials)
    
    if existing_serials:
        last_serial = existing_serials[0]["serial_number"]
        # Extract the sequence number (xxx part)
        match = re.search(r'-(\d{3})$', last_serial)
        if match:
            next_seq = int(match.group(1)) + 1
        else:
            next_seq = 1
    else:
        next_seq = 1
    
    # Format as 3-digit number with leading zeros
    serial_number = f"{today}-{next_seq:03d}"
    return serial_number

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


def main():
    st.set_page_config(
        page_title="Veterinary Animal Records",
        page_icon="🐾",
        layout="wide"
    )
    
    st.title("🐾 Veterinary Animal Records Management System")
    st.markdown("---")
    
    # Initialize MongoDB
    collection = init_mongodb()
    if collection is None:
        st.error("Unable to connect to MongoDB. Please check your connection.")
        return
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Add New Record", "Search Records", "View All Records"]
    )
    
    if page == "Add New Record":
        add_new_record_page(collection)
    elif page == "Search Records":
        search_records_page(collection)
    else:
        view_all_records_page(collection)

def add_new_record_page(collection):
    st.header("Add New Animal Record")
    
    # Choose input method
    input_method = st.radio(
        "Choose input method:",
        ["Manual Entry", "Upload Image"]
    )
    
    if input_method == "Manual Entry":
        manual_entry_form(collection)
    else:
        image_upload_form(collection)

def manual_entry_form(collection):
    """Manual entry form for animal records"""
    
    with st.form("animal_record_form"):
        st.subheader("Owner Information")
        col1, col2 = st.columns(2)
        
        with col1:
            owner_name = st.text_input("Owner's Name*", key="owner_name")
            address = st.text_area("Address", key="address")
            home_phone = st.text_input("Home Phone #", key="home_phone")
        
        with col2:
            other_phone = st.text_input("Other Phone #", key="other_phone")
            referred_by = st.text_input("Referred By", key="referred_by")
            data_entry_by = st.text_input("Data Entry By", key="data_entry_by")
        
        st.subheader("Animal Information")
        col3, col4 = st.columns(2)
        
        with col3:
            animal_name = st.text_input("Animal's Name*", key="animal_name")
            species = st.selectbox("Species", ["Dog", "Cat", "Bird", "Rabbit", "Other"], key="species")
            sex = st.selectbox("Sex", ["M", "F"], key="sex")
            age = st.text_input("Age", key="age")
        
        with col4:
            breed = st.text_input("Breed", key="breed")
            date_of_birth = st.date_input("Date of Birth", key="dob")
            colors_markings = st.text_input("Colors and Markings", key="colors_markings")
            weight = st.number_input("Weight (lbs)", min_value=0.0, key="weight")
        
        st.subheader("Treatment Records")
        
        # Treatment entries
        treatment_entries = []
        
        # Add multiple treatment entries
        num_treatments = st.number_input("Number of treatment entries", min_value=1, max_value=10, value=1)
        
        for i in range(num_treatments):
            st.write(f"**Treatment Entry {i+1}**")
            col5, col6, col7 = st.columns([1, 2, 1])
            
            with col5:
                treatment_date = st.date_input(f"Date", key=f"treatment_date_{i}")
                treatment_weight = st.number_input(f"Weight", min_value=0.0, key=f"treatment_weight_{i}")
            
            with col6:
                treatment_progress = st.text_area(f"Treatment and Progress", key=f"treatment_progress_{i}")
            
            with col7:
                charge = st.number_input(f"Charge ($)", min_value=0.0, key=f"charge_{i}")
            
            treatment_entries.append({
                "date": treatment_date.isoformat() if treatment_date else None,
                "weight": treatment_weight,
                "treatment_progress": treatment_progress,
                "charge": charge
            })
        
        st.subheader("Reminders")
        reminders = st.text_area("Reminders", key="reminders")
        
        # Submit button
        submitted = st.form_submit_button("Save Record")
        
        if submitted:
            if not owner_name or not animal_name:
                st.error("Owner's Name and Animal's Name are required!")
                return
            
            # Generate serial number
            serial_number = generate_serial_number(collection)
            
            # Prepare data for MongoDB
            record_data = {
                "serial_number": serial_number,
                "owner_name": owner_name,
                "address": address,
                "home_phone": home_phone,
                "other_phone": other_phone,
                "referred_by": referred_by,
                "data_entry_by": data_entry_by,
                "animal_name": animal_name,
                "species": species,
                "sex": sex,
                "age": age,
                "breed": breed,
                "date_of_birth": date_of_birth.isoformat() if date_of_birth else None,
                "colors_markings": colors_markings,
                "weight": weight,
                "treatment_entries": treatment_entries,
                "reminders": reminders,
                "created_at": datetime.now().isoformat(),
                "input_method": "manual"
            }
            
            # Save to MongoDB
            record_id = save_to_mongodb(record_data, collection)
            
            if record_id:
                st.success(f"Record saved successfully! Serial Number: {serial_number}")
                st.balloons()
            else:
                st.error("Failed to save record!")

def image_upload_form(collection):
    """Image upload form for animal records"""
    
    st.subheader("Upload Animal Record Image")
    
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=['png', 'jpg', 'jpeg'],
        help="Upload a photo of the animal record form"
    )
    
    if uploaded_file is not None:
        # Display the uploaded image
        image = Image.open(uploaded_file)
        image = image.rotate(-90, expand=True )
        st.image(image, caption="Portrait Mode", use_container_width=True)
        
        # Convert image to base64 for storage
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        
        # Form for additional metadata
        with st.form("image_record_form"):
            st.subheader("Additional Information")
            col1, col2 = st.columns(2)
            
            with col1:
                owner_name = st.text_input("Owner's Name (if visible)", key="img_owner_name")
                animal_name = st.text_input("Animal's Name (if visible)", key="img_animal_name")
                species = st.text_input("Species (if visible)", key="img_species")
            
            with col2:
                description = st.text_area("Description/Notes", key="img_description")
                date_uploaded = st.date_input("Date of Record", value=date.today(), key="img_date")
            
            submitted = st.form_submit_button("Save Image Record")
            
            if submitted:
                # Generate serial number
                serial_number = generate_serial_number(collection)
                
                # Prepare data for MongoDB
                record_data = {
                    "serial_number": serial_number,
                    "owner_name": owner_name,
                    "animal_name": animal_name,
                    "species": species,
                    "description": description,
                    "date_uploaded": date_uploaded.isoformat(),
                    "image_data": img_str,
                    "image_filename": uploaded_file.name,
                    "created_at": datetime.now().isoformat(),
                    "input_method": "image_upload"
                }
                
                # Save to MongoDB
                record_id = save_to_mongodb(record_data, collection)
                
                if record_id:
                    st.success(f"Image record saved successfully! Serial Number: {serial_number}")
                    st.balloons()
                else:
                    st.error("Failed to save image record!")

def search_records_page(collection):
    """Search records page"""
    st.header("Search Animal Records")
    
    search_term = st.text_input("Search by owner name, animal name, species, or breed:")
    
    if st.button("Search") or search_term:
        records = search_records(collection, search_term)
        
        if records:
            st.success(f"Found {len(records)} record(s)")
            
            for record in records:
                with st.expander(f"🐾 {record.get('animal_name', 'Unknown')} - {record.get('owner_name', 'Unknown')}"):
                    display_record(record)
        else:
            st.info("No records found.")

def view_all_records_page(collection):
    """View all records page"""
    st.header("All Animal Records")
    
    records = search_records(collection)
    
    if records:
        st.info(f"Total records: {len(records)}")
        
        # Pagination
        records_per_page = 10
        total_pages = (len(records) + records_per_page - 1) // records_per_page
        
        if total_pages > 1:
            page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
            start_idx = (page_num - 1) * records_per_page
            end_idx = start_idx + records_per_page
            page_records = records[start_idx:end_idx]
        else:
            page_records = records
        
        for record in page_records:
            record_title = f"🐾 {record.get('animal_name', 'Unknown')} - {record.get('owner_name', 'Unknown')}"
            serial_number = record.get('serial_number', 'No Serial')
            with st.expander(f"{record_title} | Serial: {serial_number}"):
                display_record(record)
    else:
        st.info("No records found.")

def display_record(record):
    """Display a single record"""
    
    # Display serial number in top right
    col_serial, col_main = st.columns([3, 1])
    with col_main:
        st.markdown(f"**Serial #:** `{record.get('serial_number', 'No Serial')}`")
    
    if record.get('input_method') == 'image_upload':
        # Display image record in A3 landscape format
        if record.get('image_data'):
            try:
                img_data = base64.b64decode(record['image_data'])
                img = Image.open(io.BytesIO(img_data))
                #rotated_image =img.rotate(-90, expand=True)
                
                # Custom CSS for A3 landscape display
                st.markdown("""
                <style>
                .a3-container {
                    width: 100%;
                    max-width: 842px;
                    margin: 0 auto;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    background-color: #f9f9f9;
                }
                .a3-image {
                    width: 100%;
                    height: auto;
                    max-height: 1191px;
                    object-fit: contain;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                }
                .record-info {
                    margin-top: 15px;
                    padding: 15px;
                    background-color: white;
                    border-radius: 4px;
                    border: 1px solid #e0e0e0;
                }
                </style>
                """, unsafe_allow_html=True)
                
                st.markdown('<div class="a3-container">', unsafe_allow_html=True)
                
                # Display image in A3 format
                # st.image(img, caption=f"Animal Record - {record.get('image_filename', 'Unknown')}", 
                #       caption="Portrait Mode", use_container_width=True, output_format='PNG')
                st.image(img, caption="Portrait Mode", use_container_width=True, output_format='PNG')
                
                # Display record information below image
                st.markdown('<div class="record-info">', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Record Information:**")
                    st.write(f"**Owner:** {record.get('owner_name', 'N/A')}")
                    st.write(f"**Animal:** {record.get('animal_name', 'N/A')}")
                    st.write(f"**Species:** {record.get('species', 'N/A')}")
                
                with col2:
                    st.write("**File Information:**")
                    st.write(f"**Filename:** {record.get('image_filename', 'N/A')}")
                    st.write(f"**Upload Date:** {record.get('date_uploaded', 'N/A')}")
                    st.write(f"**Created:** {record.get('created_at', 'N/A')}")
                
                with col3:
                    st.write("**Description:**")
                    st.write(record.get('description', 'N/A'))
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error displaying image: {e}")
        else:
            st.error("No image data found in record")
    
    else:
        # Display manual entry record
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Owner Information:**")
            st.write(f"Name: {record.get('owner_name', 'N/A')}")
            st.write(f"Address: {record.get('address', 'N/A')}")
            st.write(f"Home Phone: {record.get('home_phone', 'N/A')}")
            st.write(f"Other Phone: {record.get('other_phone', 'N/A')}")
        
        with col2:
            st.write("**Animal Information:**")
            st.write(f"Name: {record.get('animal_name', 'N/A')}")
            st.write(f"Species: {record.get('species', 'N/A')}")
            st.write(f"Breed: {record.get('breed', 'N/A')}")
            st.write(f"Sex: {record.get('sex', 'N/A')}")
            st.write(f"Age: {record.get('age', 'N/A')}")
        
        # Treatment entries
        if record.get('treatment_entries'):
            st.write("**Treatment Records:**")
            for i, treatment in enumerate(record['treatment_entries']):
                st.write(f"**Entry {i+1}:**")
                st.write(f"Date: {treatment.get('date', 'N/A')}")
                st.write(f"Weight: {treatment.get('weight', 'N/A')} lbs")
                st.write(f"Treatment: {treatment.get('treatment_progress', 'N/A')}")
                st.write(f"Charge: ${treatment.get('charge', 'N/A')}")
                st.write("---")
        
        # Reminders
        if record.get('reminders'):
            st.write(f"**Reminders:** {record.get('reminders')}")
    
    st.write(f"**Created:** {record.get('created_at', 'N/A')}")

    # Add Delete button at the bottom right
    #col_spacer, col_delete = st.columns([8, 1])
    #with col_delete:
    key_num = random.randint(100, 999)
    key=f"delete_{record.get('serial_number', '')}"
    print(key)
    col_spacer, col_delete, col_edit = st.columns([8, 1, 1])
    with col_delete:
        # if st.button("🗑️ Delete", key=f"delete_{record.get('serial_number', '')}"):
        if st.button("🗑️ Delete", key=key_num):
            collection = init_mongodb()
            result = collection.delete_one({"serial_name": record.get("serial_name")})
            if result.deleted_count:
                st.success("Record deleted successfully. Please refresh to update the list.")
            else:
                st.error("Failed to delete record.")

    with col_edit:
        #if st.button("✏️ Edit", key=f"edit_{record.get('serial_number', '')}"):
        if st.button("✏️ Edit", key=key_num + 1):
            st.session_state[f"edit_mode_{record.get('serial_number', '')}"] = True
    
    # Edit form
    if st.session_state.get(f"edit_mode_{record.get('serial_number', '')}", True):
        st.info("Edit mode enabled. Update fields and click Save.")
        with st.form(f"edit_form_{record.get('serial_number', '')}"):
            owner_name = st.text_input("Owner's Name", value=record.get("owner_name", ""))
            animal_name = st.text_input("Animal's Name", value=record.get("animal_name", ""))
            species = st.text_input("Species", value=record.get("species", ""))
            breed = st.text_input("Breed", value=record.get("breed", ""))
            age = st.text_input("Age", value=record.get("age", ""))
            reminders = st.text_area("Reminders", value=record.get("reminders", ""))
            submitted = st.form_submit_button("Save Changes")
            if submitted:
                collection = init_mongodb()
                update_fields = {
                    "owner_name": owner_name,
                    "animal_name": animal_name,
                    "species": species,
                    "breed": breed,
                    "age": age,
                    "reminders": reminders
                }
                result = collection.update_one(
                    {"serial_number": record.get("serial_number")},
                    {"$set": update_fields}
                )
                if result.modified_count:
                    st.success("Record updated successfully.")
                    st.session_state[f"edit_mode_{record.get('serial_number', '')}"] = False
                else:
                    st.error("No changes made or failed to update record.")

if __name__ == "__main__":
    main()

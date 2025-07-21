import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io
import json
import re
import datetime
from PIL import Image, ImageOps
from mongodb_manager import init_mongodb, convert_objectid_to_string, save_to_mongodb, search_records, generate_serial_number
from mongodb_manager import add_new_record_page, search_records, search_records_page, view_all_records_page, display_record

# --- Llama 3.2 API Configuration ---
def llama32_generate_content(prompt, image):
    """
    Placeholder for Llama 3.2 API call.
    Replace this with your actual Llama 3.2 inference code.
    Should return a response object with a .text attribute containing the JSON.
    """
    # Example: send prompt and image to your Llama 3.2 endpoint and get response
    response = llama32_api.generate(prompt=prompt, image=image)
    return response
    raise NotImplementedError("You must implement llama32_generate_content() to call your Llama 3.2 model.")

# --- PDF Generation Function ---
def create_animal_record_pdf(owner_info, animal_info, treatment_data_str):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    def draw_field(x, y, label, value, label_width=1.2*inch, field_width=2.5*inch):
        p.drawString(x, y + 5, f"{label}:")
        p.drawString(x + label_width, y + 5, value)
        p.line(x + label_width, y, x + label_width + field_width, y)

    p.setFont("Helvetica-Bold", 18)
    p.drawString(0.5*inch, height - 0.7*inch, "Animal Record")
    # Owner's name in bold, just below the title
    p.setFont("Helvetica-Bold", 14)
    p.drawString(0.5*inch, height - 0.95*inch, owner_info.get("Owner's Name", ""))
    # Hospital info
    p.setFont("Helvetica-Bold", 10)
    p.drawString(width - 3.5*inch, height - 0.6*inch, "WEST HIGHLAND DOG & CAT HOSPITAL")
    p.setFont("Helvetica", 9)
    p.drawString(width - 3.5*inch, height - 0.75*inch, "1795 West Highland")
    p.drawString(width - 3.5*inch, height - 0.9*inch, "San Bernardino, CA 92407")
    p.drawString(width - 3.5*inch, height - 1.05*inch, "(909) 887-5021")

    p.setFont("Helvetica-Bold", 12)
    y_pos = height - 1.5*inch
    draw_field(0.5*inch, y_pos, "Owner's Name", owner_info.get("Owner's Name", ""))
    p.setFont("Helvetica", 10)
    draw_field(4.5*inch, y_pos, "Home Phone #", owner_info.get("Home Phone #", ""), label_width=1*inch)
    y_pos -= 0.5*inch
    p.drawString(0.5*inch, y_pos + 5, "Address:")
    p.drawString(0.5*inch + 0.6*inch, y_pos + 5, owner_info.get("Address", ""))
    p.line(0.5*inch + 0.6*inch, y_pos, width - 0.5*inch, y_pos)
    y_pos -= 0.5*inch
    draw_field(4.5*inch, y_pos, "Data Entry By", owner_info.get("Data Entry By", ""), label_width=1*inch)

    y_pos -= 0.25*inch
    draw_field(0.5*inch, y_pos, "Animal's Name", animal_info.get("Animal's Name", ""))
    draw_field(4.5*inch, y_pos, "Species", animal_info.get("Species", ""), label_width=1*inch)
    y_pos -= 0.5*inch
    draw_field(0.5*inch, y_pos, "Breed", animal_info.get("Breed", ""))
    draw_field(4.5*inch, y_pos, "Colors and Markings", animal_info.get("Colors and Markings", ""), label_width=1.3*inch)
    y_pos -= 0.5*inch
    draw_field(0.5*inch, y_pos, "Sex", animal_info.get("Sex", ""))
    draw_field(4.5*inch, y_pos, "Age", animal_info.get("Age", ""), label_width=1*inch)
    y_pos -= 0.5*inch
    draw_field(0.5*inch, y_pos, "Date of Birth", animal_info.get("Date of Birth", ""))

    y_pos -= 0.5*inch
    p.drawString(0.5*inch, y_pos + 5, "Reminders:")
    p.line(0.5*inch + 0.8*inch, y_pos, width - 0.5*inch, y_pos)

    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleN.wordWrap = 'CJK'
    
    # Process treatment data from the text area
    treatment_lines = treatment_data_str.strip().split('\n')
    treatment_data = []
    for line in treatment_lines:
        parts = line.split('|')
        row = [parts[0] if len(parts) > 0 else '',
               parts[1] if len(parts) > 1 else '',
               parts[2] if len(parts) > 2 else '',
               parts[3] if len(parts) > 3 else '']
        treatment_data.append([Paragraph(cell, styleN) for cell in row])

    headers = ["Date", "Weight", "Treatment and Progress", "Charge"]
    header_row = [Paragraph(f"<b>{h}</b>", styleN) for h in headers]
    table_data = [header_row] + treatment_data
    table = Table(table_data, colWidths=[0.8*inch, 0.8*inch, 4.6*inch, 0.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    ]))
    table.wrapOn(p, width, height)
    table.drawOn(p, 0.5*inch, y_pos - 6.5*inch)

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

def extract_data_from_image(image_file):
    """
    Uses Llama 3.2 API to extract structured data from the uploaded image.
    """
    # img = Image.open(image_file)
    img = image_file  # Use the already opened PIL.Image object
    prompt = """
    Extract the information from the provided animal record image.
    Return the data as a single JSON object.
    The JSON object should have two main keys: "owner_info" and "animal_info".
    The "treatment_data" should be a single string, with each entry on a new line.
    Use the format 'Date|Weight|Treatment and Progress|Charge' for each line.
    Even though a value is not present, use an empty string with same format.

    Example format:
    {
      "owner_info": {
        "Owner's Name": "value",
        "Home Phone #": "value",
        "Other Phone #": "value",
        "Address": "value",
        "Data Entry By": "value"
      },
      "animal_info": {
        "Animal's Name": "value",
        "Species": "value",
        "Breed": "value",
        "Colors and Markings": "value",
        "Sex": "value",
        "Age": "value",
        "Date of Birth": "value"
      },
      "treatment_data": "6-9-25|19 lbs|yup rash on stomach / neck area...\\n||P fell while jumping on couch.\\n..."
    }
    """
    try:
        with st.spinner('Analyzing document with Llama 3.2...'):
            response = llama32_generate_content(prompt, img)
            # Clean up the response to extract only the JSON part
            json_str = response.text.strip().replace('```json', '').replace('```', '')
            return json.loads(json_str)
    except Exception as e:
        st.error(f"An error occurred while calling the Llama 3.2 API: {e}")
        return None

# --- Streamlit App UI ---
st.set_page_config(page_title="Llama 3.2 Animal Record Extractor", layout="wide")
st.title("📄 Animal Record Extractor & Record Generator")
st.info("Upload an animal record image, let Llama 3.2 extract the data, then edit and download it as a PDF.")

# Initialize MongoDB
collection = init_mongodb()
if collection is None:
    st.error("Unable to connect to MongoDB. Please check your connection.")

# Initialize session state
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}

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

col1, col2 = st.columns(2)

with col1:
    st.header("1. Upload Document")
    uploaded_file = st.file_uploader("Choose a JPG file", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image_bytes_for_display = uploaded_file.getvalue()
        image_for_display = Image.open(io.BytesIO(image_bytes_for_display))
        image_for_display = ImageOps.exif_transpose(image_for_display)
        st.image(image_for_display, caption="Uploaded Animal Record", use_container_width=True)
        if st.button("✨ Extract Data with Llama 3.2"):
            with st.spinner("Extracting data..."):
                extracted_data = extract_data_from_image(image_for_display)
                if extracted_data:
                    st.session_state.form_data = extracted_data
                    st.success("Data extracted successfully!")

with col2:
    st.header("2. Edit and Verify Data")
    form_data = st.session_state.form_data

    with st.form(key='record_form'):
        # --- Owner and Animal Info ---
        st.subheader("Animal Information")
        subcol0, subcol1, subcol2 = st.columns([2,1,1])
        with subcol0:
            owner_name = st.text_input("Owner's Name", value=form_data.get('owner_info', {}).get("Owner's Name", ""))
        with subcol1:
            owner_phone = st.text_input("Home Phone #", value=form_data.get('owner_info', {}).get("Home Phone #", ""))
        with subcol2:
            other_phone = st.text_input("Other Phone #", value=form_data.get('owner_info', {}).get("Other Phone #", ""))
        subcol21, subcol22 = st.columns([3,1])
        with subcol21:
            owner_address = st.text_input("Address", value=form_data.get('owner_info', {}).get("Address", ""))
        with subcol22:
            data_entry_by = st.text_input("Data Entry By", value = form_data.get('owner_info', {}).get("Data Entry By", ""))
        subcol3, subcol4, subcol5 = st.columns([2,1,1])
        with subcol3:
            animal_name = st.text_input("Animal's Name", value=form_data.get('animal_info', {}).get("Animal's Name", ""))
        with subcol4:
            animal_species = st.text_input("Species", value=form_data.get('animal_info', {}).get("Species", ""))
        with subcol5:
            animal_breed = st.text_input("Breed", value=form_data.get('animal_info', {}).get("Breed", ""))
        subcol16, subcoll7, subcoll8 = st.columns(3)
        with subcol16:
            animal_sex = st.text_input("Sex", value=form_data.get('animal_info', {}).get("Sex", ""))
        with subcoll7:
            animal_age = st.text_input("Age", value=form_data.get('animal_info', {}).get("Age", ""))
        with subcoll8:
            animal_color = st.text_input("Colors and Markings", value=form_data.get('animal_info', {}).get("Colors and Markings", ""))
        subcol31, subcol32, subcol33 = st.columns(3)
        with subcol31:
            reminder1 = st.text_input("reminder 1", " ", key="reminder1")
        with subcol32:
            reminder2 = st.text_input("reminder 2", " ", key="reminder2")
        with subcol33:
            reminder3 = st.text_input("reminder 3", " ", key="reminder3")
        st.subheader("Treatment and Progress")
        treatment_text = st.text_area("Notes (Format: Date|Weight|Progress|Charge)", 
                                      value=form_data.get('treatment_data', ""), 
                                      height=400)

        submit_button = st.form_submit_button(label='Save Changes')

    if submit_button:
        if not owner_name or not animal_name:
            st.error("Owner's Name and Animal's Name are required!")
        else:
            serial_number = generate_serial_number(collection)
            record_data = {
                "serial_number": serial_number,
                "owner_name": owner_name,
                "address": owner_address,
                "home_phone": owner_phone,
                "other_phone": other_phone,
                "data_entry_by": data_entry_by,
                "animal_name": animal_name,
                "animal_species": animal_species,
                "animal_sex": animal_sex,
                "animal_age": animal_age,
                "animal_breed": animal_breed,
                "animal_color": animal_color,
                "treatment_entries": treatment_text,
                "reminders": [reminder1, reminder2, reminder3],
                "created_at": datetime.datetime.now().isoformat()
            }
            record_id = save_to_mongodb(record_data, collection)
            if record_id:
                st.success(f"Record saved successfully! Serial Number: {serial_number}")
                st.balloons()
            else:
                st.error("Failed to save record!")

    st.header("3. Download PDF")
    if owner_name and animal_name:
        owner_data_for_pdf = {
            "Owner's Name": owner_name,
            "Home Phone #": owner_phone,
            "Address": owner_address,
            "Data Entry By": data_entry_by
        }
        animal_data_for_pdf = {
            "Animal's Name": animal_name,
            "Species": animal_species,
            "Breed": animal_breed,
            "Colors and Markings": animal_color,
            "Sex": animal_sex,
            "Age": animal_age,
            "Date of Birth": "" # This field was empty
        }
        pdf_file = create_animal_record_pdf(owner_data_for_pdf, animal_data_for_pdf, treatment_text)
        st.download_button(
            label="⬇️ Download Animal Record as PDF",
            data=pdf_file,
            file_name=f"Animal-Record-{animal_name or 'Unknown'}.pdf",
            mime="application/pdf"
        )
    else:
        st.warning("Please extract or enter data before downloading.")
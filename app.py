# ==========================================
# File: app.py
"""
Main application entry point with Streamlit UI
"""
import streamlit as st
from soap_note_manager import SOAPNoteManager

def get_next_patient_id(manager):
    """Generate next patient ID as Pxxxx (xxxx: 0001-9999)"""
    patients = manager.db_manager.patients_collection.find().sort("patient_id", -1)
    last_id = None
    for p in patients:
        last_id = p["patient_id"]
        break
    if last_id and last_id.startswith("P"):
        num = int(last_id[1:])
        next_num = num + 1
    else:
        next_num = 1
    return f"P{next_num:04d}"

def main():
    """Main function to run the SOAP notes application with Streamlit UI"""
    st.set_page_config(page_title="Medical SOAP Notes Manager", layout="centered")
    st.title("Medical SOAP Notes Manager")

    # Initialize the manager in session state
    if "manager" not in st.session_state:
        st.session_state.manager = SOAPNoteManager()
        st.session_state.manager.add_patient("P0001", "John Doe", "1980-05-15", "555-1234")
        st.session_state.manager.add_doctor("D001", "Dr. Smith", "Family Medicine", "555-5678")

    manager = st.session_state.manager

    menu = [
        "Start new note",
        "Manual Dictation",
        "Voice Dictation",
        "Save current note",
        "View patient notes",
        "Search notes",
        "Test microphone",
        "Add Patient",
        "Exit"
    ]

    choice = st.sidebar.radio("Menu", menu)

    if choice == "Start new note":
        with st.form("start_note_form"):
            patient_id = st.text_input("Enter patient ID")
            doctor_id = st.text_input("Enter doctor ID")
            submitted = st.form_submit_button("Start Note")
            if submitted:
                manager.start_new_note(patient_id, doctor_id)
                st.success(f"Started new note for patient {patient_id} by doctor {doctor_id}")

    elif choice == "Manual Dictation":
        
        # subjective = st.text_area("Subjective")
        subjective = st.text_area("Subjective", key="subjective_text")
        if st.button("🎤 Dictate Subjective"):
            recognized_text = manager.speech_manager.listen_for_speech()
            if recognized_text:
                st.session_state["subjective_text"] = recognized_text
                st.success("Dictation complete! Text inserted into Subjective.")
        with st.form("manual_dictation_form"):   
            objective = st.text_area("Objective")
            assessment = st.text_area("Assessment")
            plan = st.text_area("Plan")
            submitted = st.form_submit_button("Add to Note")
            if submitted:
                manager.manual_dictation(subjective, objective, assessment, plan)
        
    
    
    elif choice == "Voice Dictation":
        if st.button("Begin Voice Dictation"):
            manager.start_voice_dictation_session()
            st.info("Voice Dictation session started.")
        
            

    elif choice == "Save current note":
        if st.button("Save Note"):
            manager.save_note()
            st.success("Current note saved.")

    elif choice == "View patient notes":
        with st.form("view_notes_form"):
            patient_id = st.text_input("Enter patient ID to view notes")
            submitted = st.form_submit_button("View Notes")
            if submitted:
                notes = manager.get_patient_notes(patient_id)
                st.write(f"Found {len(notes)} notes for patient {patient_id}")
                for note in notes:
                    st.write(f"Date: {note['date']}, Doctor: {note['doctor_id']}")

    elif choice == "Search notes":
        with st.form("search_notes_form"):
            query = st.text_input("Enter search query")
            submitted = st.form_submit_button("Search")
            if submitted:
                notes = manager.search_notes(query)
                st.write(f"Found {len(notes)} notes matching '{query}'")
                for note in notes:
                    st.write(f"Patient: {note['patient_id']}, Date: {note['date']}")

    elif choice == "Test microphone":
        if st.button("Test Microphone"):
            manager.speech_manager.test_microphone()
            st.info("Microphone test initiated.")

    elif choice == "Add Patient":
        with st.form("add_patient_form"):
            next_patient_id = get_next_patient_id(manager)
            st.write(f"Assigned Patient ID: {next_patient_id}")  # Display the generated ID
            name = st.text_input("Name")
            dob = st.date_input("Date of Birth")
            contact = st.text_input("Contact (optional)")
            submitted = st.form_submit_button("Add Patient")
            if submitted:
                dob_str = dob.strftime("%Y-%m-%d")
                success = manager.add_patient(next_patient_id, name, dob_str, contact)
                if success:
                    st.success(f"Patient {name} added successfully with ID {next_patient_id}!")
                else:
                    st.error(f"Failed to add patient {next_patient_id}. It may already exist.")
    elif choice == "Exit":
        st.warning("To exit, please close the Streamlit app.")

if __name__ == "__main__":
    main()
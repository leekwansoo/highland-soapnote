# ==========================================
# File: soap_note_manager.py
"""
Main SOAP note management system
"""
from datetime import datetime
from typing import Optional, List, Dict
from models import SOAPNote, Patient, Doctor, SpeakerType, TranscriptEntry
from database_manager import DatabaseManager
from speech_recognition_manager import SpeechRecognitionManager
from text_processor import TextProcessor
import streamlit as st

class SOAPNoteManager:
    def __init__(self, mongodb_uri: str = "mongodb://localhost:27017/", db_name: str = "medical_records"):
        """Initialize the SOAP Note Manager with all components"""
        self.db_manager = DatabaseManager(mongodb_uri, db_name)
        self.speech_manager = SpeechRecognitionManager()
        self.text_processor = TextProcessor()
        
        # Current session variables
        self.current_note: Optional[SOAPNote] = None
        self.current_speaker = SpeakerType.DOCTOR
    
    def add_patient(self, patient_id: str, name: str, dob: str, contact: str = "") -> bool:
        """Add a new patient"""
        patient = Patient(patient_id, name, dob, contact)
        return self.db_manager.add_patient(patient)
    
    def add_doctor(self, doctor_id: str, name: str, specialty: str = "", contact: str = "") -> bool:
        """Add a new doctor"""
        doctor = Doctor(doctor_id, name, specialty, contact)
        return self.db_manager.add_doctor(doctor)
    
    def start_new_note(self, patient_id: str, doctor_id: str) -> bool:
        """Start a new SOAP note session"""
        # Verify patient and doctor exist
        patient = self.db_manager.get_patient(patient_id)
        doctor = self.db_manager.get_doctor(doctor_id)
        
        if not patient:
            st.write(f"Patient {patient_id} not found")
            return False
        
        if not doctor:
            st.write(f"Doctor {doctor_id} not found")
            return False
        
        self.current_note = SOAPNote(
            patient_id=patient_id,
            doctor_id=doctor_id,
            date=datetime.now()
        )
        
        st.write(f"New SOAP note started for patient {patient_id} with doctor {doctor_id}")
        return True
    
    def add_dictation_to_note(self, text: str, speaker: SpeakerType, section: str = "") -> bool:
        """Add dictated text to the current SOAP note"""
        if not self.current_note:
            st.write("No active SOAP note. Please start a new note first.")
            return False
        
        timestamp = datetime.now()
        
        # Create transcript entry
        transcript_entry = TranscriptEntry(
            timestamp=timestamp,
            speaker=speaker.value,
            text=text,
            section=section
        )
        
        # Add to raw transcript
        self.current_note.add_transcript_entry(transcript_entry)
        
        # Process and categorize the text
        categorized_section = self.text_processor.categorize_text(text, self.current_note, section)
        
        st.write(f"Added dictation from {speaker.value} to {categorized_section}: {text[:50]}...")
        return True
    
    def manual_dictation(self, subjective: str, objective: str, assessment: str, plan: str) -> bool:
        """Add typed dictation to the current SOAP note sections."""
        if not self.current_note:
            st.write("No active SOAP note. Please start a new note first.")
            return False

        # Add each section if provided
        if subjective:
            self.add_dictation_to_note(subjective, self.current_speaker, "subjective")
            self.current_note.subjective = subjective
        if objective:
            self.add_dictation_to_note(objective, self.current_speaker, "objective")
            self.current_note.objective = objective
        if assessment:
            self.add_dictation_to_note(assessment, self.current_speaker, "assessment")
            self.current_note.assessment = assessment
        if plan:
            self.add_dictation_to_note(plan, self.current_speaker, "plan")
            self.current_note.plan = plan

        st.success("Typed dictation added to SOAP note.")
        return True

    

    def start_voice_dictation_session(self):
        """Start an interactive dictation session"""
        if not self.current_note:
            st.write("No active SOAP note. Please start a new note first.")
            return
        
        st.write("\n=== DICTATION SESSION STARTED ===")
        st.sidebar.write("Commands:")
        st.sidebar.write("- 'doctor' or 'patient' - Switch speaker")
        st.sidebar.write("- 'subjective', 'objective', 'assessment', 'plan' - Set section")
        st.sidebar.write("- 'save' - Save current note")
        st.sidebar.write("- 'quit' - End session")
        st.sidebar.write("- Just speak normally to add dictation")
        st.sidebar.write("=====================================\n")
        
        current_section = ""
        
        while True:
            try:
                st.write(f"\nCurrent speaker: {self.current_speaker.value}")
                if current_section:
                    st.write(f"Current section: {current_section}")
                
                text = self.speech_manager.listen_for_speech()
                
                if text:
                    text_lower = text.lower()
                    
                    # Handle commands
                    if text_lower in ["doctor", "dr"]:
                        self.current_speaker = SpeakerType.DOCTOR
                        st.write("Switched to doctor")
                        continue
                    elif text_lower in ["patient", "pt"]:
                        self.current_speaker = SpeakerType.PATIENT
                        st.write("Switched to patient")
                        continue
                    elif text_lower in ["subjective", "subject"]:
                        current_section = "subjective"
                        st.write("Section set to subjective")
                        continue
                    elif text_lower in ["objective", "object"]:
                        current_section = "objective"
                        st.write("Section set to objective")
                        continue
                    elif text_lower in ["assessment", "assess"]:
                        current_section = "assessment"
                        st.write("Section set to assessment")
                        continue
                    elif text_lower in ["plan"]:
                        current_section = "plan"
                        st.write("Section set to plan")
                        continue
                    elif text_lower in ["save"]:
                        self.save_note()
                        continue
                    elif text_lower in ["quit", "exit", "stop"]:
                        st.write("Ending dictation session")
                        break
                    
                    # Add dictation to note
                    self.add_dictation_to_note(text, self.current_speaker, current_section)
                
            except KeyboardInterrupt:
                st.write("\nDictation session interrupted")
                break
    def stop_dictation_session(self):
        """Stop the current dictation session."""
        # Add your logic to stop dictation here
        # For example, if you have a speech_manager:
        if hasattr(self, "speech_manager"):
            self.speech_manager.stop_listening = True  # Or your actual stop logic
        st.write("Dictation session stopped.")

    def save_note(self) -> bool:
        """Save the current SOAP note"""
        if not self.current_note:
            st.write("No active SOAP note to save")
            return False
        
        success = self.db_manager.save_soap_note(self.current_note)
        if success:
            self.print_note_summary()
            self.current_note = None
        return success
    
    def print_note_summary(self):
        """Print a summary of the current SOAP note"""
        if not self.current_note:
            st.write("No active SOAP note")
            return
        
        st.write("\n" + "="*50)
        st.write("SOAP NOTE SUMMARY")
        st.write("="*50)
        st.write(f"Patient ID: {self.current_note.patient_id}")
        st.write(f"Doctor ID: {self.current_note.doctor_id}")
        st.write(f"Date: {self.current_note.date.strftime('%Y-%m-%d %H:%M:%S')}")
        st.write("\nSUBJECTIVE:")
        st.write(self.current_note.subjective or "No subjective data")
        st.write("\nOBJECTIVE:")
        st.write(self.current_note.objective or "No objective data")
        st.write("\nASSESSMENT:")
        st.write(self.current_note.assessment or "No assessment data")
        st.write("\nPLAN:")
        st.write(self.current_note.plan or "No plan data")
        st.write("="*50)
    
    def get_patient_notes(self, patient_id: str, limit: int = 10) -> List[Dict]:
        """Get SOAP notes for a specific patient"""
        return self.db_manager.get_patient_notes(patient_id, limit)
    
    def search_notes(self, query: str, field: str = "all") -> List[Dict]:
        """Search SOAP notes by text content"""
        return self.db_manager.search_notes(query, field)
    
    def close(self):
        """Close all connections and cleanup"""
        self.db_manager.close_connection()


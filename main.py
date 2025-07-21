# ==========================================
# File: main.py
"""
Main application entry point
"""
from soap_note_manager import SOAPNoteManager

def main():
    """Main function to run the SOAP notes application"""
    # Initialize the manager
    manager = SOAPNoteManager()
    
    # Add sample data
    manager.add_patient("P001", "John Doe", "1980-05-15", "555-1234")
    manager.add_doctor("D001", "Dr. Smith", "Family Medicine", "555-5678")
    
    print("Medical SOAP Notes Manager")
    print("1. Start new note")
    print("2. Begin dictation session")
    print("3. Save current note")
    print("4. View patient notes")
    print("5. Search notes")
    print("6. Test microphone")
    print("7. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == "1":
            patient_id = input("Enter patient ID: ").strip()
            doctor_id = input("Enter doctor ID: ").strip()
            manager.start_new_note(patient_id, doctor_id)
        
        elif choice == "2":
            manager.start_dictation_session()
        
        elif choice == "3":
            manager.save_note()
        
        elif choice == "4":
            patient_id = input("Enter patient ID: ").strip()
            notes = manager.get_patient_notes(patient_id)
            print(f"\nFound {len(notes)} notes for patient {patient_id}")
            for note in notes:
                print(f"Date: {note['date']}, Doctor: {note['doctor_id']}")
        
        elif choice == "5":
            query = input("Enter search query: ").strip()
            notes = manager.search_notes(query)
            print(f"\nFound {len(notes)} notes matching '{query}'")
            for note in notes:
                print(f"Patient: {note['patient_id']}, Date: {note['date']}")
        
        elif choice == "6":
            manager.speech_manager.test_microphone()
        
        elif choice == "7":
            manager.close()
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
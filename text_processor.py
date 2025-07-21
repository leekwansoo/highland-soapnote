# File: text_processor.py
"""
Text processing and SOAP categorization
"""
from typing import List
from models import SOAPNote

class TextProcessor:
    def __init__(self):
        """Initialize text processing with keyword mappings"""
        self.subjective_keywords = [
            "patient reports", "complains of", "states", "feels", "describes", 
            "history", "symptoms", "pain", "discomfort", "experienced"
        ]
        
        self.objective_keywords = [
            "vital signs", "blood pressure", "temperature", "examination", 
            "observed", "physical", "heart rate", "respiratory", "weight"
        ]
        
        self.assessment_keywords = [
            "diagnosis", "impression", "assessment", "likely", "rule out", 
            "differential", "condition", "disorder", "disease"
        ]
        
        self.plan_keywords = [
            "plan", "treatment", "medication", "follow up", "prescribe", 
            "recommend", "therapy", "surgery", "procedure"
        ]
    
    def categorize_text(self, text: str, soap_note: SOAPNote, section: str = "") -> str:
        """
        Categorize text into appropriate SOAP section
        
        Args:
            text: Input text to categorize
            soap_note: SOAP note object to update
            section: Explicitly specified section (optional)
            
        Returns:
            The section where text was categorized
        """
        text_lower = text.lower()
        
        # If section is explicitly specified, use it
        if section:
            section_lower = section.lower()
            if section_lower == "subjective":
                soap_note.subjective += f" {text}"
                return "subjective"
            elif section_lower == "objective":
                soap_note.objective += f" {text}"
                return "objective"
            elif section_lower == "assessment":
                soap_note.assessment += f" {text}"
                return "assessment"
            elif section_lower == "plan":
                soap_note.plan += f" {text}"
                return "plan"
        
        # Auto-categorize based on keywords
        if self._contains_keywords(text_lower, self.subjective_keywords):
            soap_note.subjective += f" {text}"
            return "subjective"
        elif self._contains_keywords(text_lower, self.objective_keywords):
            soap_note.objective += f" {text}"
            return "objective"
        elif self._contains_keywords(text_lower, self.assessment_keywords):
            soap_note.assessment += f" {text}"
            return "assessment"
        elif self._contains_keywords(text_lower, self.plan_keywords):
            soap_note.plan += f" {text}"
            return "plan"
        else:
            # Default to subjective if no clear category
            soap_note.subjective += f" {text}"
            return "subjective"
    
    def _contains_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the specified keywords"""
        return any(keyword in text for keyword in keywords)
    
    def add_custom_keywords(self, section: str, keywords: List[str]):
        """Add custom keywords for a specific section"""
        if section.lower() == "subjective":
            self.subjective_keywords.extend(keywords)
        elif section.lower() == "objective":
            self.objective_keywords.extend(keywords)
        elif section.lower() == "assessment":
            self.assessment_keywords.extend(keywords)
        elif section.lower() == "plan":
            self.plan_keywords.extend(keywords)

# ==========================================



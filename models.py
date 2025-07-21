# File: models.py
"""
Data models for the Medical SOAP Notes system
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

class SpeakerType(Enum):
    DOCTOR = "doctor"
    PATIENT = "patient"

@dataclass
class Patient:
    patient_id: str
    name: str
    date_of_birth: str
    contact: str = ""
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Doctor:
    doctor_id: str
    name: str
    specialty: str = ""
    contact: str = ""
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self):
        return asdict(self)

@dataclass
class TranscriptEntry:
    timestamp: datetime
    speaker: str
    text: str
    section: str = ""
    
    def to_dict(self):
        return asdict(self)

@dataclass
class SOAPNote:
    patient_id: str
    doctor_id: str
    date: datetime
    subjective: str = ""
    objective: str = ""
    assessment: str = ""
    plan: str = ""
    raw_transcript: List[Dict] = None
    
    def __post_init__(self):
        if self.raw_transcript is None:
            self.raw_transcript = []
    
    def to_dict(self):
        return asdict(self)
    
    def add_transcript_entry(self, entry: TranscriptEntry):
        self.raw_transcript.append(entry.to_dict())
    
    def clean_fields(self):
        """Clean up whitespace in text fields"""
        self.subjective = self.subjective.strip()
        self.objective = self.objective.strip()
        self.assessment = self.assessment.strip()
        self.plan = self.plan.strip()

# ==========================================

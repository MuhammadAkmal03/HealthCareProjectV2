from pydantic import BaseModel, Field, model_validator
from typing import List, Optional


# --- Schemas for Symptom Prediction ---
class SymptomPredictionRequest(BaseModel):
    Age: int = Field(..., ge=18, le=80, description="Age must be between 18 and 80 (based on training data)")
    Gender: str
    Heart_Rate_bpm: int = Field(..., ge=50, le=130, description="Heart rate must be between 50 and 130 bpm")
    Body_Temperature_C: float = Field(..., ge=35.0, le=41.0, description="Temperature must be between 35°C and 41°C")
    oxygen_saturation_percent: float = Field(..., alias="Oxygen_Saturation_%", ge=85.0, le=100.0, description="Oxygen saturation must be between 85% and 100%")
    Systolic_BP: int = Field(..., ge=85, le=185, description="Systolic BP must be between 85 and 185 (dataset: 90-179)")
    Diastolic_BP: int = Field(..., ge=55, le=125, description="Diastolic BP must be between 55 and 125 (dataset: 60-119)")
    symptoms: List[str]
    model_config = {"populate_by_name": True}


class SymptomPredictionResponse(BaseModel):
    predicted_diagnosis: str


# --- Schemas for Scan Analyzer ---
class ScanAnalysisRequest(BaseModel):
    image_base64: str


class ScanAnalysisResponse(BaseModel):
    predicted_condition: str
    confidence_score: float


# SCHEMAS FOR THE AI ASSISTANT MODULE 

# --- Chatbot Schemas ---
class ChatRequest(BaseModel):
    question: str
    chat_history: List[List[str]] = []  # Default to empty list


class ChatResponse(BaseModel):
    answer: str


# --- Summarizer Schemas ---
class SummarizeRequest(BaseModel):
    pdf_base64: Optional[str] = None
    raw_text: Optional[str] = None

    @model_validator(mode="after")
    def check_one_input(self):
        if sum(x is not None for x in [self.pdf_base64, self.raw_text]) != 1:
            raise ValueError(
                'Exactly one of "pdf_base64" or "raw_text" must be provided.'
            )
        return self


class SummarizeResponse(BaseModel):
    summary: str

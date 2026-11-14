from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    query: str = Field(..., description="Fault code or technician query text (e.g. 'FC 4103 traction converter overheat')")
    train_type: Optional[str] = Field(None, description="Train model/class filter (e.g. 'Class 700')")
    subsystem: Optional[str] = Field(None, description="Train subsystem filter (e.g. 'Traction', 'Doors', 'Brakes', 'HVAC')")
    similarity_top_k: Optional[int] = Field(5, ge=1, le=10)

class CitationSource(BaseModel):
    manual_name: str
    section: Optional[str] = None
    page: Optional[int] = None
    source_file: Optional[str] = None
    url: Optional[str] = None
    text_snippet: str
    score: Optional[float] = None

class QueryResponse(BaseModel):
    answer: str
    found_in_manuals: bool
    citations: List[CitationSource] = []
    fault_code_detected: Optional[str] = None

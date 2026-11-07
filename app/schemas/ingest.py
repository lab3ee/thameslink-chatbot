from typing import Optional, List, Literal
from pydantic import BaseModel, Field

class IngestRequest(BaseModel):
    train_type: Optional[str] = Field(
        None,
        description="Target train class (e.g. 'Class 700'). Leave blank for general reference documents."
    )
    subsystem: Optional[str] = Field(
        None,
        description="Subsystem (e.g. 'Traction', 'Doors'). Leave blank for general reference documents."
    )
    document_category: Literal["fleet_manual", "general_reference"] = Field(
        "fleet_manual",
        description=(
            "Use 'fleet_manual' for documents tied to a specific train type and subsystem. "
            "Use 'general_reference' for rulebooks, standards, or policy documents that apply across all fleets."
        )
    )
    manual_name: Optional[str] = Field(None, description="Optional custom manual name")
    file_path: Optional[str] = Field(None, description="Path relative to data/manuals or specific file")

class IngestResponse(BaseModel):
    status: str
    documents_processed: int
    chunks_indexed: int
    train_type: str
    subsystem: str
    document_category: str
    errors: List[str] = []

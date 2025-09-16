"""Data models for EE recommendations."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class InefficiencySymptom(BaseModel):
    """Detected inefficiency symptom from benchmarking results."""
    
    symptom_id: str = Field(description="Unique identifier for the symptom")
    description: str = Field(description="Human-readable description")
    severity: Optional[float] = Field(None, description="Severity score (0-1)")
    detected_value: Optional[float] = Field(None, description="The value that triggered detection")
    threshold_value: Optional[float] = Field(None, description="The threshold used for detection")
    metric: Optional[str] = Field(None, description="Metric name (e.g., 'baseload', 'cooling_slope')")


class EEMeasureRecommendation(BaseModel):
    """Energy efficiency measure recommendation."""
    
    measure_id: str = Field(description="Unique identifier matching Django Measure.measure_id")
    name: str = Field(description="Short name of the measure")
    triggered_by: List[str] = Field(description="List of symptom_ids that triggered this recommendation")
    priority: Optional[str] = Field(None, description="Priority level: high, medium, low")
    

class EERecommendationResult(BaseModel):
    """Complete EE recommendation result."""
    
    symptoms: List[InefficiencySymptom] = Field(description="Detected inefficiency symptoms")
    recommendations: List[EEMeasureRecommendation] = Field(description="Recommended EE measures")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")

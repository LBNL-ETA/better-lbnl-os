"""Data models for EE recommendations."""

from pydantic import BaseModel, Field


class InefficiencySymptom(BaseModel):
    """Detected inefficiency symptom from benchmarking results."""

    symptom_id: str = Field(description="Unique identifier for the symptom")
    description: str = Field(description="Human-readable description")
    severity: float | None = Field(None, description="Severity score (0-1)")
    detected_value: float | None = Field(None, description="The value that triggered detection")
    threshold_value: float | None = Field(None, description="The threshold used for detection")
    metric: str | None = Field(None, description="Metric name (e.g., 'baseload', 'cooling_slope')")


class EEMeasureRecommendation(BaseModel):
    """Energy efficiency measure recommendation."""

    measure_id: str = Field(description="Unique identifier matching Django Measure.measure_id")
    name: str = Field(description="Short name of the measure")
    triggered_by: list[str] = Field(
        description="List of symptom_ids that triggered this recommendation"
    )
    priority: str | None = Field(None, description="Priority level: high, medium, low")


class EERecommendationResult(BaseModel):
    """Complete EE recommendation result."""

    symptoms: list[InefficiencySymptom] = Field(description="Detected inefficiency symptoms")
    recommendations: list[EEMeasureRecommendation] = Field(description="Recommended EE measures")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

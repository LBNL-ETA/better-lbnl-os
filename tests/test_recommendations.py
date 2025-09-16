"""Tests for the EE recommendation engine."""

import pytest
from better_lbnl_os.core.recommendations import (
    detect_symptoms,
    map_symptoms_to_measures,
    recommend_ee_measures,
    BETTER_MEASURES
)
from better_lbnl_os.models.benchmarking import (
    BenchmarkStatistics,
    BenchmarkResult,
    ChangePointResult,
    EnergyStatistics,
    StatValue
)
from better_lbnl_os.models.recommendations import (
    InefficiencySymptom,
    EEMeasureRecommendation,
    EERecommendationResult
)
from better_lbnl_os.constants import BuildingSpaceType


class TestSymptomDetection:
    """Test symptom detection from benchmarking results."""

    def test_high_electricity_baseload(self):
        """Test detection of high electricity baseload symptom."""
        # Create benchmark result with high baseload
        benchmark_result = BenchmarkResult(
            results={
                'electricity': ChangePointResult(
                    baseload=0.5,  # High baseload
                    cooling_slope=0.01,
                    heating_slope=-0.01,
                    cooling_change_point=15.0,
                    heating_change_point=10.0,
                    r2=0.85,
                    rmse=0.05,
                    model_type='3PC'
                )
            },
            metadata={'units': 'kWh/sqm'}
        )

        # Create reference statistics with lower baseload
        reference_stats = BenchmarkStatistics(
            electricity=EnergyStatistics(
                baseload=StatValue(median=0.2, stdev=0.1),
                cooling_slope=StatValue(median=0.01, stdev=0.005)
            )
        )

        # Detect symptoms
        symptoms = detect_symptoms(benchmark_result, reference_stats)

        # Should detect high baseload symptom
        assert any(s.symptom_id == 'high_elec_baseload' for s in symptoms)
        symptom = next(s for s in symptoms if s.symptom_id == 'high_elec_baseload')
        assert symptom.severity > 0.5
        assert symptom.detected_value == 0.5

    def test_high_cooling_sensitivity(self):
        """Test detection of high cooling sensitivity symptom."""
        benchmark_result = BenchmarkResult(
            results={
                'electricity': ChangePointResult(
                    baseload=0.2,
                    cooling_slope=0.03,  # High cooling slope
                    heating_slope=-0.01,
                    cooling_change_point=15.0,
                    heating_change_point=10.0,
                    r2=0.85,
                    rmse=0.05,
                    model_type='3PC'
                )
            },
            metadata={'units': 'kWh/sqm'}
        )

        reference_stats = BenchmarkStatistics(
            electricity=EnergyStatistics(
                baseload=StatValue(median=0.2, stdev=0.1),
                cooling_slope=StatValue(median=0.01, stdev=0.005)
            )
        )

        symptoms = detect_symptoms(benchmark_result, reference_stats)
        assert any(s.symptom_id == 'high_cooling_sensitivity' for s in symptoms)

    def test_irregular_consumption(self):
        """Test detection of irregular consumption patterns."""
        benchmark_result = BenchmarkResult(
            results={
                'electricity': ChangePointResult(
                    baseload=0.2,
                    cooling_slope=0.01,
                    heating_slope=-0.01,
                    cooling_change_point=15.0,
                    heating_change_point=10.0,
                    r2=0.5,  # Poor model fit
                    rmse=0.15,
                    model_type='3PC'
                )
            },
            metadata={'units': 'kWh/sqm'}
        )

        symptoms = detect_symptoms(benchmark_result)
        assert any(s.symptom_id == 'irregular_consumption' for s in symptoms)

    def test_simultaneous_heating_cooling(self):
        """Test detection of simultaneous heating and cooling."""
        benchmark_result = BenchmarkResult(
            results={
                'electricity': ChangePointResult(
                    baseload=0.2,
                    cooling_slope=0.02,  # Positive cooling slope
                    heating_slope=-0.01,
                    cooling_change_point=15.0,
                    heating_change_point=10.0,
                    r2=0.85,
                    rmse=0.05,
                    model_type='3PC'
                ),
                'fossil_fuel': ChangePointResult(
                    baseload=0.1,
                    cooling_slope=0.01,  # Also positive - simultaneous operation
                    heating_slope=-0.02,
                    cooling_change_point=18.0,
                    heating_change_point=12.0,
                    r2=0.80,
                    rmse=0.06,
                    model_type='3PC'
                )
            },
            metadata={'units': 'kWh/sqm'}
        )

        symptoms = detect_symptoms(benchmark_result)
        assert any(s.symptom_id == 'simultaneous_heating_cooling' for s in symptoms)


class TestMeasureMapping:
    """Test mapping of symptoms to EE measures."""

    def test_high_baseload_measures(self):
        """Test measures recommended for high baseload."""
        symptoms = [
            InefficiencySymptom(
                symptom_id='high_elec_baseload',
                description='High electricity baseload',
                severity=0.7
            )
        ]

        measures = map_symptoms_to_measures(symptoms)

        # Should recommend lighting, plug loads, and controls
        measure_ids = {m.measure_id for m in measures}
        assert 'lighting_upgrade' in measure_ids
        assert 'plug_load_reduction' in measure_ids
        assert 'hvac_controls' in measure_ids

    def test_cooling_sensitivity_measures(self):
        """Test measures for high cooling sensitivity."""
        symptoms = [
            InefficiencySymptom(
                symptom_id='high_cooling_sensitivity',
                description='High cooling sensitivity',
                severity=0.8
            )
        ]

        measures = map_symptoms_to_measures(symptoms)

        measure_ids = {m.measure_id for m in measures}
        assert 'cooling_system' in measure_ids
        assert 'envelope_insulation' in measure_ids
        assert 'window_upgrade' in measure_ids

    def test_heating_sensitivity_measures(self):
        """Test measures for high heating sensitivity."""
        symptoms = [
            InefficiencySymptom(
                symptom_id='high_heating_sensitivity',
                description='High heating sensitivity',
                severity=0.8
            )
        ]

        measures = map_symptoms_to_measures(symptoms)

        measure_ids = {m.measure_id for m in measures}
        assert 'heating_system' in measure_ids
        assert 'envelope_air_sealing' in measure_ids
        assert 'envelope_insulation' in measure_ids

    def test_industrial_specific_measures(self):
        """Test building-type specific recommendations."""
        symptoms = [
            InefficiencySymptom(
                symptom_id='high_elec_baseload',
                description='High electricity baseload',
                severity=0.7
            )
        ]

        measures = map_symptoms_to_measures(
            symptoms,
            building_type=BuildingSpaceType.MANUFACTURING_INDUSTRIAL_PLANT
        )

        measure_ids = {m.measure_id for m in measures}
        assert 'compressed_air' in measure_ids
        assert 'motor_drives' in measure_ids

    def test_priority_ordering(self):
        """Test that measures are ordered by priority."""
        symptoms = [
            InefficiencySymptom(
                symptom_id='high_elec_baseload',
                description='High baseload',
                severity=0.7
            ),
            InefficiencySymptom(
                symptom_id='high_cooling_sensitivity',
                description='High cooling',
                severity=0.8
            )
        ]

        measures = map_symptoms_to_measures(symptoms)

        # Check that high priority measures come first
        priorities = [m.priority for m in measures]
        assert priorities == sorted(priorities, key=lambda p: {'high': 0, 'medium': 1, 'low': 2}.get(p, 3))


class TestIntegratedRecommendation:
    """Test the complete recommendation flow."""

    def test_full_recommendation_workflow(self):
        """Test complete workflow from benchmarking to recommendations."""
        # Create comprehensive benchmark result
        benchmark_result = BenchmarkResult(
            results={
                'electricity': ChangePointResult(
                    baseload=0.4,  # High
                    cooling_slope=0.025,  # High
                    heating_slope=-0.008,
                    cooling_change_point=20.0,  # Abnormal
                    heating_change_point=10.0,
                    r2=0.65,  # Poor fit
                    rmse=0.08,
                    model_type='3PC'
                ),
                'fossil_fuel': ChangePointResult(
                    baseload=0.05,  # High
                    cooling_slope=0.002,
                    heating_slope=-0.03,  # High
                    cooling_change_point=22.0,
                    heating_change_point=15.0,
                    r2=0.75,
                    rmse=0.06,
                    model_type='3PC'
                )
            },
            metadata={'units': 'kWh/sqm'}
        )

        # Create reference statistics
        reference_stats = BenchmarkStatistics(
            electricity=EnergyStatistics(
                baseload=StatValue(median=0.2, stdev=0.1),
                cooling_slope=StatValue(median=0.01, stdev=0.005),
                heating_slope=StatValue(median=-0.01, stdev=0.005),
                cooling_change_point=StatValue(median=15.0, stdev=3.0),
                heating_change_point=StatValue(median=12.0, stdev=3.0)
            ),
            fossil_fuel=EnergyStatistics(
                baseload=StatValue(median=0.02, stdev=0.01),
                cooling_slope=StatValue(median=0.001, stdev=0.0005),
                heating_slope=StatValue(median=-0.02, stdev=0.01),
                cooling_change_point=StatValue(median=20.0, stdev=3.0),
                heating_change_point=StatValue(median=17.0, stdev=3.0)
            )
        )

        # Generate recommendations
        result = recommend_ee_measures(
            benchmark_result,
            reference_stats,
            building_type=BuildingSpaceType.OFFICE
        )

        # Verify result structure
        assert isinstance(result, EERecommendationResult)
        assert len(result.symptoms) > 0
        assert len(result.recommendations) > 0

        # Check metadata
        assert result.metadata['total_symptoms'] == len(result.symptoms)
        assert result.metadata['total_recommendations'] == len(result.recommendations)
        assert result.metadata['building_type'] == 'Office'
        assert result.metadata['reference_used'] is True

        # Verify symptoms detected
        symptom_ids = {s.symptom_id for s in result.symptoms}
        assert 'high_elec_baseload' in symptom_ids
        assert 'high_cooling_sensitivity' in symptom_ids
        assert 'irregular_consumption' in symptom_ids

        # Verify measures recommended
        measure_ids = {m.measure_id for m in result.recommendations}
        assert 'lighting_upgrade' in measure_ids
        assert 'hvac_controls' in measure_ids
        assert 'cooling_system' in measure_ids

    def test_custom_thresholds(self):
        """Test using custom thresholds for symptom detection."""
        benchmark_result = BenchmarkResult(
            results={
                'electricity': ChangePointResult(
                    baseload=0.3,  # Slightly high
                    cooling_slope=0.015,
                    heating_slope=-0.01,
                    cooling_change_point=15.0,
                    heating_change_point=10.0,
                    r2=0.85,
                    rmse=0.05,
                    model_type='3PC'
                )
            },
            metadata={'units': 'kWh/sqm'}
        )

        reference_stats = BenchmarkStatistics(
            electricity=EnergyStatistics(
                baseload=StatValue(median=0.2, stdev=0.1),
                cooling_slope=StatValue(median=0.01, stdev=0.005)
            )
        )

        # With default thresholds (1.5x), baseload is not high enough
        result_default = recommend_ee_measures(benchmark_result, reference_stats)
        assert not any(s.symptom_id == 'high_elec_baseload' for s in result_default.symptoms)

        # With custom threshold (1.2x), baseload is detected as high
        custom_thresholds = {'high_baseload_factor': 1.2}
        result_custom = recommend_ee_measures(
            benchmark_result,
            reference_stats,
            custom_thresholds=custom_thresholds
        )
        assert any(s.symptom_id == 'high_elec_baseload' for s in result_custom.symptoms)

    def test_no_reference_stats(self):
        """Test recommendations without reference statistics."""
        benchmark_result = BenchmarkResult(
            results={
                'electricity': ChangePointResult(
                    baseload=0.3,
                    cooling_slope=0.02,
                    heating_slope=-0.01,
                    cooling_change_point=15.0,
                    heating_change_point=10.0,
                    r2=0.45,  # Poor fit - will trigger irregular consumption
                    rmse=0.12,
                    model_type='3PC'
                )
            },
            metadata={'units': 'kWh/sqm'}
        )

        # Generate recommendations without reference
        result = recommend_ee_measures(benchmark_result)

        # Should still detect symptoms that don't require reference
        symptom_ids = {s.symptom_id for s in result.symptoms}
        assert 'irregular_consumption' in symptom_ids

        # Should still provide recommendations
        assert len(result.recommendations) > 0
        assert result.metadata['reference_used'] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""Demonstration of benchmarking functionality in better-lbnl-os.

This script shows how to:
1. Create change-point models
2. Generate benchmark statistics from a group of buildings
3. Benchmark an individual building against the statistics
4. Interpret the results
"""

from better_lbnl_os.models.results import ChangePointModelResult

from better_lbnl_os.core.benchmarking import (
    benchmark_building,
    create_statistics_from_models,
)


def main():
    print("=== BETTER-LBNL Benchmarking Demo ===\n")

    # 1. Create sample change-point models representing a reference dataset
    print("1. Creating reference dataset of change-point models...")

    reference_models = [
        ChangePointModelResult(
            heating_slope=-0.015,
            heating_change_point=16.0,
            baseload=1.8,
            cooling_change_point=22.0,
            cooling_slope=0.025,
            r_squared=0.85,
            cvrmse=0.18,
            model_type="5P",
        ),
        ChangePointModelResult(
            heating_slope=-0.012,
            heating_change_point=15.5,
            baseload=2.2,
            cooling_change_point=23.0,
            cooling_slope=0.030,
            r_squared=0.78,
            cvrmse=0.22,
            model_type="5P",
        ),
        ChangePointModelResult(
            heating_slope=-0.018,
            heating_change_point=17.0,
            baseload=1.9,
            cooling_change_point=21.5,
            cooling_slope=0.020,
            r_squared=0.82,
            cvrmse=0.19,
            model_type="5P",
        ),
        ChangePointModelResult(
            heating_slope=-0.014,
            heating_change_point=16.5,
            baseload=2.0,
            cooling_change_point=22.5,
            cooling_slope=0.028,
            r_squared=0.80,
            cvrmse=0.20,
            model_type="5P",
        ),
    ]

    building_ids = [f"ref_building_{i+1}" for i in range(len(reference_models))]
    print(f"Created {len(reference_models)} reference building models\n")

    # 2. Generate benchmark statistics from the reference dataset
    print("2. Generating benchmark statistics...")

    benchmark_stats = create_statistics_from_models(reference_models, building_ids)

    print("Electricity Benchmarks:")
    if benchmark_stats.ELECTRICITY:
        elec = benchmark_stats.ELECTRICITY
        if elec.baseload:
            print(f"  Baseload: median={elec.baseload.median:.3f}, stdev={elec.baseload.stdev:.3f}")
        if elec.cooling_change_point:
            print(
                f"  Cooling CP: median={elec.cooling_change_point.median:.1f}°C, stdev={elec.cooling_change_point.stdev:.1f}"
            )
        if elec.cooling_slope:
            print(
                f"  Cooling Slope: median={elec.cooling_slope.median:.4f}, stdev={elec.cooling_slope.stdev:.4f}"
            )

    print("\nFossil Fuel Benchmarks:")
    if benchmark_stats.FOSSIL_FUEL:
        fossil = benchmark_stats.FOSSIL_FUEL
        if fossil.baseload:
            print(
                f"  Baseload: median={fossil.baseload.median:.3f}, stdev={fossil.baseload.stdev:.3f}"
            )
        if fossil.heating_change_point:
            print(
                f"  Heating CP: median={fossil.heating_change_point.median:.1f}°C, stdev={fossil.heating_change_point.stdev:.1f}"
            )
        if fossil.heating_slope:
            print(
                f"  Heating Slope: median={fossil.heating_slope.median:.4f}, stdev={fossil.heating_slope.stdev:.4f}"
            )

    print("\n" + "=" * 60 + "\n")

    # 3. Create a test building to benchmark
    print("3. Creating test building to benchmark...")

    test_building_models = {
        "ELECTRICITY": ChangePointModelResult(
            heating_slope=None,
            heating_change_point=None,
            baseload=2.5,  # Higher than median (worse performance)
            cooling_change_point=20.0,  # Lower than median (worse performance)
            cooling_slope=0.035,  # Higher than median (worse performance)
            r_squared=0.75,
            cvrmse=0.25,
            model_type="3P-C",
        ),
        "FOSSIL_FUEL": ChangePointModelResult(
            heating_slope=-0.010,  # Less negative than median (worse performance)
            heating_change_point=18.0,  # Higher than median (worse performance)
            baseload=2.3,  # Higher than median (worse performance)
            cooling_change_point=None,
            cooling_slope=None,
            r_squared=0.77,
            cvrmse=0.23,
            model_type="3P-H",
        ),
    }

    print("Test building characteristics:")
    print(f"  ELECTRICITY: {test_building_models['ELECTRICITY'].model_type} model")
    print(f"    Baseload: {test_building_models['ELECTRICITY'].baseload}")
    print(f"    Cooling CP: {test_building_models['ELECTRICITY'].cooling_change_point}°C")
    print(f"    Cooling Slope: {test_building_models['ELECTRICITY'].cooling_slope}")

    print(f"  FOSSIL_FUEL: {test_building_models['FOSSIL_FUEL'].model_type} model")
    print(f"    Baseload: {test_building_models['FOSSIL_FUEL'].baseload}")
    print(f"    Heating CP: {test_building_models['FOSSIL_FUEL'].heating_change_point}°C")
    print(f"    Heating Slope: {test_building_models['FOSSIL_FUEL'].heating_slope}")

    print("\n" + "=" * 60 + "\n")

    # 4. Benchmark the test building
    print("4. Benchmarking test building...")

    benchmark_result = benchmark_building(
        change_point_results=test_building_models,
        benchmark_statistics=benchmark_stats,
        floor_area=5000.0,  # 5000 sq ft building
        savings_target="NOMINAL",
        building_id="test_building_001",
    )

    # 5. Display results
    print("5. Benchmark Results:\n")

    print(f"Building ID: {benchmark_result.building_id}")
    print(f"Floor Area: {benchmark_result.floor_area:,.0f} sq ft")
    print(f"Savings Target: {benchmark_result.savings_target}")

    print("\nELECTRICITY Performance:")
    if benchmark_result.ELECTRICITY:
        elec_result = benchmark_result.ELECTRICITY

        if elec_result.baseload:
            bl = elec_result.baseload
            print("  Baseload:")
            print(f"    Current: {bl.coefficient_value:.3f}")
            print(f"    Rating: {bl.rating}")
            print(f"    Percentile: {bl.percentile:.1f}%")
            print(f"    Target: {bl.target_value:.3f}")

        if elec_result.cooling_change_point:
            ccp = elec_result.cooling_change_point
            print("  Cooling Change Point:")
            print(f"    Current: {ccp.coefficient_value:.1f}°C")
            print(f"    Rating: {ccp.rating}")
            print(f"    Percentile: {ccp.percentile:.1f}%")
            print(f"    Target: {ccp.target_value:.1f}°C")

        if elec_result.cooling_slope:
            cs = elec_result.cooling_slope
            print("  Cooling Slope:")
            print(f"    Current: {cs.coefficient_value:.4f}")
            print(f"    Rating: {cs.rating}")
            print(f"    Percentile: {cs.percentile:.1f}%")
            print(f"    Target: {cs.target_value:.4f}")

    print("\nFOSSIL FUEL Performance:")
    if benchmark_result.FOSSIL_FUEL:
        fossil_result = benchmark_result.FOSSIL_FUEL

        if fossil_result.baseload:
            bl = fossil_result.baseload
            print("  Baseload:")
            print(f"    Current: {bl.coefficient_value:.3f}")
            print(f"    Rating: {bl.rating}")
            print(f"    Percentile: {bl.percentile:.1f}%")
            print(f"    Target: {bl.target_value:.3f}")

        if fossil_result.heating_change_point:
            hcp = fossil_result.heating_change_point
            print("  Heating Change Point:")
            print(f"    Current: {hcp.coefficient_value:.1f}°C")
            print(f"    Rating: {hcp.rating}")
            print(f"    Percentile: {hcp.percentile:.1f}%")
            print(f"    Target: {hcp.target_value:.1f}°C")

        if fossil_result.heating_slope:
            hs = fossil_result.heating_slope
            print("  Heating Slope:")
            print(f"    Current: {hs.coefficient_value:.4f}")
            print(f"    Rating: {hs.rating}")
            print(f"    Percentile: {hs.percentile:.1f}%")
            print(f"    Target: {hs.target_value:.4f}")

    # 6. Overall assessment
    print("\n" + "=" * 60)
    print("6. Overall Assessment:")

    elec_rating = benchmark_result.get_overall_rating("ELECTRICITY")
    fossil_rating = benchmark_result.get_overall_rating("FOSSIL_FUEL")

    elec_percentile = benchmark_result.get_average_percentile("ELECTRICITY")
    fossil_percentile = benchmark_result.get_average_percentile("FOSSIL_FUEL")

    print(f"\nElectricity Overall Rating: {elec_rating}")
    if elec_percentile:
        print(f"Electricity Average Percentile: {elec_percentile:.1f}%")

    print(f"\nFossil Fuel Overall Rating: {fossil_rating}")
    if fossil_percentile:
        print(f"Fossil Fuel Average Percentile: {fossil_percentile:.1f}%")

    print("\nInterpretation:")
    print("- 'Good' rating means better than 84% of reference buildings")
    print("- 'Typical' rating means within 1 standard deviation of median")
    print("- 'Poor' rating means worse than 84% of reference buildings")
    print("- Higher percentiles indicate better performance")
    print("- Target values show potential for improvement")


if __name__ == "__main__":
    main()

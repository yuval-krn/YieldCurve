#!/usr/bin/env python3
"""
Test script to verify the new ingestion and transformation approach.
"""

from sqlmodel import Session, select, desc
from app import engine, ChartDataPoint, transform_and_store_treasury_data

def test_transform_and_store():
    """Test the transform_and_store_treasury_data function."""

    print("Testing transform_and_store_treasury_data function...")

    # Sample BC values (like what comes from XML parsing)
    sample_bc_values = {
        "BC_1MONTH": 4.20,
        "BC_3MONTH": 4.03,
        "BC_6MONTH": 3.95,
        "BC_1YEAR": 3.61,
        "BC_2YEAR": 3.45,
        "BC_3YEAR": 3.52,
        "BC_5YEAR": 3.74,
        "BC_7YEAR": 3.91,
        "BC_10YEAR": 4.11,
        "BC_20YEAR": 4.45,
        "BC_30YEAR": 4.72,
        "BC_UNKNOWN": 1.0,  # Should be ignored (not in label_map)
    }

    test_date = "2025-01-01T00:00:00"

    with Session(engine) as session:
        # Clear any existing test data for this date
        existing_points = session.exec(
            select(ChartDataPoint).where(ChartDataPoint.date == test_date)
        ).all()
        for point in existing_points:
            session.delete(point)
        session.commit()

        # Test the transformation and storage
        transform_and_store_treasury_data(test_date, sample_bc_values, session)
        session.commit()

        # Verify the data was stored correctly
        stored_points = session.exec(
            select(ChartDataPoint)
            .where(ChartDataPoint.date == test_date)
            .order_by(ChartDataPoint.term)
        ).all()

        print(f"✅ Stored {len(stored_points)} chart data points")

        # Check the expected terms and values
        expected_mappings = {
            "BC_1MONTH": ("1m", 4.20),
            "BC_3MONTH": ("3m", 4.03),
            "BC_6MONTH": ("6m", 3.95),
            "BC_1YEAR": ("1Y", 3.61),
            "BC_2YEAR": ("2Y", 3.45),
            "BC_3YEAR": ("3Y", 3.52),
            "BC_5YEAR": ("5Y", 3.74),
            "BC_7YEAR": ("7Y", 3.91),
            "BC_10YEAR": ("10Y", 4.11),
            "BC_20YEAR": ("20Y", 4.45),
            "BC_30YEAR": ("30Y", 4.72),
        }

        # Verify each expected point exists
        print(f"\nStored chart data points:")
        for point in stored_points:
            print(f"  {point.term:4s}: {point.yield_value}%")

        # Verify mappings
        stored_by_term = {point.term: point.yield_value for point in stored_points}

        all_correct = True
        for bc_key, (expected_term, expected_value) in expected_mappings.items():
            if expected_term in stored_by_term:
                actual_value = stored_by_term[expected_term]
                if abs(actual_value - expected_value) < 0.001:  # Float comparison
                    print(f"  ✅ {bc_key} -> {expected_term}: {actual_value}% (correct)")
                else:
                    print(f"  ❌ {bc_key} -> {expected_term}: expected {expected_value}%, got {actual_value}%")
                    all_correct = False
            else:
                print(f"  ❌ Missing term: {expected_term}")
                all_correct = False

        # Check that unknown BC fields were ignored
        unknown_terms = [point.term for point in stored_points if point.term not in [t[0] for t in expected_mappings.values()]]
        if not unknown_terms:
            print(f"  ✅ Unknown BC fields properly ignored")
        else:
            print(f"  ❌ Unexpected terms found: {unknown_terms}")
            all_correct = False

        # Clean up test data
        for point in stored_points:
            session.delete(point)
        session.commit()

        return all_correct

def test_with_none_values():
    """Test the function handles None values properly."""

    print("\n" + "="*60)
    print("Testing with None values...")

    sample_bc_values_with_nones = {
        "BC_1MONTH": None,  # Should be ignored
        "BC_3MONTH": 4.03,  # Should be stored
        "BC_6MONTH": None,  # Should be ignored
        "BC_1YEAR": 3.61,   # Should be stored
        "BC_10YEAR": None,  # Should be ignored
        "BC_30YEAR": 4.72,  # Should be stored
    }

    test_date = "2025-01-02T00:00:00"

    with Session(engine) as session:
        # Clear any existing test data
        existing_points = session.exec(
            select(ChartDataPoint).where(ChartDataPoint.date == test_date)
        ).all()
        for point in existing_points:
            session.delete(point)
        session.commit()

        # Test with None values
        transform_and_store_treasury_data(test_date, sample_bc_values_with_nones, session)
        session.commit()

        # Verify only non-None values were stored
        stored_points = session.exec(
            select(ChartDataPoint)
            .where(ChartDataPoint.date == test_date)
            .order_by(ChartDataPoint.term)
        ).all()

        expected_stored_terms = ["3m", "1Y", "30Y"]  # Only the non-None values
        actual_stored_terms = [point.term for point in stored_points]

        print(f"Expected terms: {expected_stored_terms}")
        print(f"Actual terms: {actual_stored_terms}")

        if set(actual_stored_terms) == set(expected_stored_terms):
            print("✅ None values properly ignored")
            success = True
        else:
            print("❌ None value handling failed")
            success = False

        # Verify stored values are correct
        expected_values = {"3m": 4.03, "1Y": 3.61, "30Y": 4.72}
        for point in stored_points:
            expected_value = expected_values.get(point.term)
            if expected_value and abs(point.yield_value - expected_value) < 0.001:
                print(f"✅ {point.term}: {point.yield_value}% (correct)")
            else:
                print(f"❌ {point.term}: expected {expected_value}, got {point.yield_value}")
                success = False

        # Clean up test data
        for point in stored_points:
            session.delete(point)
        session.commit()

        return success

def test_api_format():
    """Test that the stored data can be retrieved in the expected API format."""

    print("\n" + "="*60)
    print("Testing API format compatibility...")

    test_date = "2025-01-03T00:00:00"

    # Sample data that should create a complete yield curve
    complete_bc_values = {
        "BC_1MONTH": 4.20,
        "BC_3MONTH": 4.03,
        "BC_6MONTH": 3.95,
        "BC_1YEAR": 3.61,
        "BC_2YEAR": 3.45,
        "BC_3YEAR": 3.52,
        "BC_5YEAR": 3.74,
        "BC_7YEAR": 3.91,
        "BC_10YEAR": 4.11,
        "BC_20YEAR": 4.45,
        "BC_30YEAR": 4.72,
    }

    with Session(engine) as session:
        # Clear and store test data
        existing_points = session.exec(
            select(ChartDataPoint).where(ChartDataPoint.date == test_date)
        ).all()
        for point in existing_points:
            session.delete(point)
        session.commit()

        transform_and_store_treasury_data(test_date, complete_bc_values, session)
        session.commit()

        # Retrieve data as the API would
        chart_data_points = session.exec(
            select(ChartDataPoint).where(ChartDataPoint.date == test_date)
        ).all()

        # Convert to API format
        chart_data = []
        for point in chart_data_points:
            chart_data.append({
                "term": point.term,
                "Yield": point.yield_value
            })

        # Sort in expected order (as the API does)
        order = ["1m", "3m", "6m", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
        chart_data.sort(key=lambda x: order.index(x["term"]) if x["term"] in order else 999)

        print(f"API-formatted chart data:")
        for i, point in enumerate(chart_data):
            print(f"  {i+1:2d}. {point['term']:4s}: {point['Yield']}%")

        # Verify the structure matches expected API response
        expected_structure = all(
            isinstance(point, dict) and
            "term" in point and
            "Yield" in point and
            isinstance(point["term"], str) and
            isinstance(point["Yield"], (int, float))
            for point in chart_data
        )

        expected_terms = ["1m", "3m", "6m", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
        actual_terms = [point["term"] for point in chart_data]

        if expected_structure:
            print("✅ Chart data structure is valid for API")
        else:
            print("❌ Chart data structure is invalid")

        if actual_terms == expected_terms:
            print("✅ Chart data is properly ordered")
        else:
            print("❌ Chart data ordering is incorrect")
            print(f"   Expected: {expected_terms}")
            print(f"   Actual:   {actual_terms}")

        # Clean up
        for point in chart_data_points:
            session.delete(point)
        session.commit()

        return expected_structure and (actual_terms == expected_terms)

if __name__ == "__main__":
    print("🧪 Testing new ingestion and transformation approach\n")

    # Run all tests
    test1_success = test_transform_and_store()
    test2_success = test_with_none_values()
    test3_success = test_api_format()

    print("\n" + "="*60)
    print("📊 Test Results Summary:")
    print(f"  Transform and Store: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"  None Value Handling: {'✅ PASS' if test2_success else '❌ FAIL'}")
    print(f"  API Format Compatibility: {'✅ PASS' if test3_success else '❌ FAIL'}")

    if all([test1_success, test2_success, test3_success]):
        print("\n🏁 All tests passed! New ingestion approach is working correctly.")
    else:
        print("\n❌ Some tests failed. Please review the implementation.")

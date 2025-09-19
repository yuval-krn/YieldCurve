#!/usr/bin/env python3
"""
Test script to verify the API endpoints for treasury data with the new database approach.
"""

import httpx
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

async def test_root_endpoint():
    """Test the root endpoint that returns latest treasury data."""
    print("Testing root endpoint (/)...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Root endpoint successful")
                print(f"   Date: {data.get('date')}")
                print(f"   Chart data points: {len(data.get('chart_data', []))}")

                # Show first few chart data points
                chart_data = data.get('chart_data', [])
                if chart_data:
                    print("   Sample yields:")
                    for point in chart_data[:5]:
                        print(f"     {point.get('term')}: {point.get('Yield')}%")

                # Verify structure
                expected_structure = all(
                    isinstance(point, dict) and
                    'term' in point and
                    'Yield' in point
                    for point in chart_data
                )

                if expected_structure:
                    print("   ✅ Chart data structure is valid")
                else:
                    print("   ❌ Chart data structure is invalid")

                return data
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None

        except Exception as e:
            print(f"❌ Error calling root endpoint: {e}")
            return None

async def test_treasury_dates_endpoint():
    """Test the treasury dates endpoint."""
    print("\nTesting treasury dates endpoint (/treasury/dates/)...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/treasury/dates/")

            if response.status_code == 200:
                data = response.json()
                dates = data.get('dates', [])
                print(f"✅ Treasury dates endpoint successful")
                print(f"   Available dates: {len(dates)}")

                if dates:
                    print(f"   Latest date: {dates[0]}")
                    print(f"   Earliest date: {dates[-1]}")
                    print("   First 5 dates:")
                    for date in dates[:5]:
                        print(f"     {date}")

                return dates
            else:
                print(f"❌ Treasury dates endpoint failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None

        except Exception as e:
            print(f"❌ Error calling treasury dates endpoint: {e}")
            return None

async def test_treasury_by_date_endpoint(test_date: str = None):
    """Test the treasury by date endpoint."""
    print(f"\nTesting treasury by date endpoint (/treasury/{{date}})...")

    # If no test_date provided, try to get one from dates endpoint
    if not test_date:
        async with httpx.AsyncClient() as client:
            dates_response = await client.get(f"{BASE_URL}/treasury/dates/")
            if dates_response.status_code == 200:
                dates = dates_response.json().get('dates', [])
                test_date = dates[0] if dates else None

    if not test_date:
        print("❌ No test date available")
        return None

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/treasury/{test_date}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Treasury by date endpoint successful")
                print(f"   Date: {data.get('date')}")
                chart_data = data.get('chart_data', [])
                print(f"   Chart data points: {len(chart_data)}")

                if chart_data:
                    print("   Yield curve data:")
                    for point in chart_data:
                        print(f"     {point.get('term'):4s}: {point.get('Yield')}%")

                # Verify structure matches root endpoint
                expected_structure = all(
                    isinstance(point, dict) and
                    'term' in point and
                    'Yield' in point
                    for point in chart_data
                )

                if expected_structure:
                    print("   ✅ Chart data structure matches expected format")
                else:
                    print("   ❌ Chart data structure is invalid")

                return data
            elif response.status_code == 404:
                print(f"⚠️  No data found for date {test_date}")
                return None
            else:
                print(f"❌ Treasury by date endpoint failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None

        except Exception as e:
            print(f"❌ Error calling treasury by date endpoint: {e}")
            return None

async def test_treasury_invalid_date_endpoint():
    """Test the treasury endpoint with invalid date."""
    print("\nTesting treasury endpoint with invalid date...")

    async with httpx.AsyncClient() as client:
        try:
            # Test with non-existent date
            invalid_date = "2024-12-31T00:00:00"
            response = await client.get(f"{BASE_URL}/treasury/{invalid_date}")

            if response.status_code == 404:
                print(f"✅ Invalid date properly returns 404")
                return True
            else:
                print(f"❌ Expected 404 but got: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error calling treasury endpoint with invalid date: {e}")
            return False

async def test_treasury_all_chart_data_endpoint():
    """Test the treasury all chart data endpoint with pagination."""
    print("\nTesting treasury all chart data endpoint (/treasury/)...")

    async with httpx.AsyncClient() as client:
        try:
            # Test with default pagination
            response = await client.get(f"{BASE_URL}/treasury/")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Treasury all chart data endpoint successful")
                print(f"   Records returned: {len(data)}")

                if data:
                    first_record = data[0]
                    print(f"   Latest record: {first_record.get('date')} - {first_record.get('term')}: {first_record.get('yield_value')}%")

                # Test with pagination
                paginated_response = await client.get(f"{BASE_URL}/treasury/?limit=10&offset=0")
                if paginated_response.status_code == 200:
                    paginated_data = paginated_response.json()
                    print(f"   Pagination test (limit=10): {len(paginated_data)} records")

                    # Verify structure
                    if paginated_data:
                        sample_record = paginated_data[0]
                        required_fields = ['date', 'term', 'yield_value']
                        has_fields = all(field in sample_record for field in required_fields)

                        if has_fields:
                            print("   ✅ Record structure is valid")
                        else:
                            print("   ❌ Record structure is missing required fields")

                return data
            else:
                print(f"❌ Treasury all chart data endpoint failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None

        except Exception as e:
            print(f"❌ Error calling treasury all chart data endpoint: {e}")
            return None

def compare_data_consistency(root_data, by_date_data):
    """Compare data from root endpoint vs by-date endpoint for consistency."""
    print("\nComparing data consistency between endpoints...")

    if not root_data or not by_date_data:
        print("❌ Cannot compare - missing data from one or both endpoints")
        return False

    root_date = root_data.get('date')
    by_date_date = by_date_data.get('date')

    if root_date != by_date_date:
        print(f"❌ Date mismatch: root={root_date}, by_date={by_date_date}")
        return False

    root_chart = root_data.get('chart_data', [])
    by_date_chart = by_date_data.get('chart_data', [])

    if len(root_chart) != len(by_date_chart):
        print(f"❌ Chart data length mismatch: root={len(root_chart)}, by_date={len(by_date_chart)}")
        return False

    # Compare each data point
    root_by_term = {point['term']: point['Yield'] for point in root_chart}
    by_date_by_term = {point['term']: point['Yield'] for point in by_date_chart}

    for term in root_by_term:
        if term not in by_date_by_term:
            print(f"❌ Term {term} missing from by-date endpoint")
            return False

        if abs(root_by_term[term] - by_date_by_term[term]) > 0.001:
            print(f"❌ Yield mismatch for {term}: root={root_by_term[term]}, by_date={by_date_by_term[term]}")
            return False

    print("✅ Data consistency verified between root and by-date endpoints")
    return True

def print_performance_summary(chart_data_length):
    """Print information about the performance benefits."""
    print(f"\n📈 Performance Benefits Summary:")
    print(f"   • Pre-computed chart data points in database")
    print(f"   • No real-time transformation needed")
    print(f"   • {chart_data_length} data points served instantly")
    print(f"   • Consistent ordering maintained in database")
    print(f"   • Efficient querying by date or term")

async def main():
    """Run all API tests."""
    print("🧪 Starting API endpoint tests for new database approach...\n")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("Run: uvicorn app:app --reload\n")

    # Test treasury endpoints
    root_data = await test_root_endpoint()
    dates_data = await test_treasury_dates_endpoint()

    # Use the latest date from dates endpoint for testing by-date endpoint
    test_date = None
    if dates_data and len(dates_data) > 0:
        test_date = dates_data[0]

    by_date_data = await test_treasury_by_date_endpoint(test_date)
    await test_treasury_invalid_date_endpoint()
    all_chart_data = await test_treasury_all_chart_data_endpoint()

    # Compare consistency between endpoints
    if root_data and by_date_data:
        compare_data_consistency(root_data, by_date_data)

    # Test orders endpoints
    created_order = await test_create_order_endpoint()
    await test_order_validation()
    orders_data = await test_get_orders_endpoint()
    workflow_success = await test_order_workflow()
    await test_yield_validation()

    # Print performance summary
    if root_data and 'chart_data' in root_data:
        print_performance_summary(len(root_data['chart_data']))

async def test_create_order_endpoint():
    """Test the order creation endpoint with various scenarios."""
    print("\nTesting order creation endpoint (POST /orders/)...")

    async with httpx.AsyncClient() as client:
        # First get current treasury data to use in our test
        treasury_response = await client.get(f"{BASE_URL}/")
        if treasury_response.status_code != 200:
            print("❌ Cannot test orders - treasury data unavailable")
            return None

        treasury_data = treasury_response.json()
        chart_data = treasury_data.get('chart_data', [])
        if not chart_data:
            print("❌ Cannot test orders - no chart data available")
            return None

        # Use first chart data point for testing
        test_point = chart_data[0]
        term = test_point['term']
        yield_value = test_point['Yield']

        # Test valid order creation
        valid_order = {
            "term": term,
            "yield": yield_value,
            "quantity": 10000.0
        }

        try:
            response = await client.post(f"{BASE_URL}/orders/", json=valid_order)

            if response.status_code == 200:
                order_data = response.json()
                print(f"✅ Valid order creation successful")
                print(f"   Order ID: {order_data.get('id')}")
                print(f"   Term: {order_data.get('term')}")
                print(f"   Yield: {order_data.get('yield_value')}%")
                print(f"   Quantity: ${order_data.get('quantity'):,.0f}")
                print(f"   Issue Date: {order_data.get('issue_date')}")
                print(f"   Maturity Date: {order_data.get('maturity_date')}")

                # Verify response structure
                required_fields = ['id', 'term', 'yield_value', 'quantity', 'issue_date', 'purchase_timestamp', 'maturity_date']
                missing_fields = [field for field in required_fields if field not in order_data]

                if not missing_fields:
                    print("   ✅ Order response structure is valid")
                else:
                    print(f"   ❌ Missing fields in response: {missing_fields}")

                return order_data
            else:
                print(f"❌ Valid order creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None

        except Exception as e:
            print(f"❌ Error creating valid order: {e}")
            return None

async def test_order_validation():
    """Test order validation with invalid inputs."""
    print("\nTesting order validation...")

    async with httpx.AsyncClient() as client:
        # Test invalid term
        invalid_term_order = {
            "term": "INVALID_TERM",
            "yield": 4.0,
            "quantity": 1000.0
        }

        try:
            response = await client.post(f"{BASE_URL}/orders/", json=invalid_term_order)
            if response.status_code == 422:  # Pydantic validation error
                print("✅ Invalid term properly rejected")
            else:
                print(f"❌ Invalid term validation failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing invalid term: {e}")

        # Test invalid yield (negative)
        invalid_yield_order = {
            "term": "1Y",
            "yield": -1.0,
            "quantity": 1000.0
        }

        try:
            response = await client.post(f"{BASE_URL}/orders/", json=invalid_yield_order)
            if response.status_code == 422:
                print("✅ Invalid yield properly rejected")
            else:
                print(f"❌ Invalid yield validation failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing invalid yield: {e}")

        # Test invalid quantity (zero)
        invalid_quantity_order = {
            "term": "1Y",
            "yield": 4.0,
            "quantity": 0
        }

        try:
            response = await client.post(f"{BASE_URL}/orders/", json=invalid_quantity_order)
            if response.status_code == 422:
                print("✅ Invalid quantity properly rejected")
            else:
                print(f"❌ Invalid quantity validation failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing invalid quantity: {e}")

        # Test missing required field
        incomplete_order = {
            "term": "1Y",
            "yield": 4.0
            # Missing quantity
        }

        try:
            response = await client.post(f"{BASE_URL}/orders/", json=incomplete_order)
            if response.status_code == 422:
                print("✅ Missing field properly rejected")
            else:
                print(f"❌ Missing field validation failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing missing field: {e}")

async def test_get_orders_endpoint():
    """Test the get orders endpoint."""
    print("\nTesting get orders endpoint (GET /orders/)...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/orders/")

            if response.status_code == 200:
                orders = response.json()
                print(f"✅ Get orders endpoint successful")
                print(f"   Orders returned: {len(orders)}")

                if orders:
                    first_order = orders[0]
                    print(f"   Latest order: {first_order.get('term')} - ${first_order.get('quantity'):,.0f}")

                    # Verify order structure
                    required_fields = ['id', 'term', 'yield_value', 'quantity', 'issue_date', 'purchase_timestamp', 'maturity_date']
                    has_all_fields = all(field in first_order for field in required_fields)

                    if has_all_fields:
                        print("   ✅ Order structure is valid")
                    else:
                        missing = [f for f in required_fields if f not in first_order]
                        print(f"   ❌ Missing order fields: {missing}")

                # Test pagination
                paginated_response = await client.get(f"{BASE_URL}/orders/?limit=5&offset=0")
                if paginated_response.status_code == 200:
                    paginated_orders = paginated_response.json()
                    print(f"   Pagination test (limit=5): {len(paginated_orders)} orders")

                return orders
            else:
                print(f"❌ Get orders endpoint failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None

        except Exception as e:
            print(f"❌ Error calling get orders endpoint: {e}")
            return None

async def test_order_workflow():
    """Test complete order workflow: create order then retrieve it."""
    print("\nTesting complete order workflow...")

    async with httpx.AsyncClient() as client:
        # Get current treasury data
        treasury_response = await client.get(f"{BASE_URL}/")
        if treasury_response.status_code != 200:
            print("❌ Cannot test workflow - treasury data unavailable")
            return False

        treasury_data = treasury_response.json()
        chart_data = treasury_data.get('chart_data', [])
        if not chart_data:
            print("❌ Cannot test workflow - no chart data")
            return False

        # Create a test order
        test_point = chart_data[0]
        test_order = {
            "term": test_point['term'],
            "yield": test_point['Yield'],
            "quantity": 5000.0
        }

        # Step 1: Create order
        create_response = await client.post(f"{BASE_URL}/orders/", json=test_order)
        if create_response.status_code != 200:
            print(f"❌ Order creation failed in workflow: {create_response.status_code}")
            return False

        created_order = create_response.json()
        order_id = created_order['id']
        print(f"✅ Step 1: Order created with ID {order_id}")

        # Step 2: Retrieve all orders and verify our order is there
        get_response = await client.get(f"{BASE_URL}/orders/")
        if get_response.status_code != 200:
            print(f"❌ Order retrieval failed in workflow: {get_response.status_code}")
            return False

        all_orders = get_response.json()
        our_order = next((order for order in all_orders if order['id'] == order_id), None)

        if our_order:
            print(f"✅ Step 2: Order retrieved successfully")
            print(f"   Term: {our_order['term']}")
            print(f"   Yield: {our_order['yield_value']}%")
            print(f"   Quantity: ${our_order['quantity']:,.0f}")
        else:
            print(f"❌ Step 2: Created order not found in orders list")
            return False

        # Step 3: Verify order data integrity
        if (our_order['term'] == test_order['term'] and
            our_order['yield_value'] == test_order['yield'] and
            our_order['quantity'] == test_order['quantity']):
            print("✅ Step 3: Order data integrity verified")
            return True
        else:
            print("❌ Step 3: Order data integrity check failed")
            return False

async def test_yield_validation():
    """Test that orders are validated against current market yields."""
    print("\nTesting yield validation against market data...")

    async with httpx.AsyncClient() as client:
        # Get current treasury data
        treasury_response = await client.get(f"{BASE_URL}/")
        if treasury_response.status_code != 200:
            print("❌ Cannot test yield validation - treasury data unavailable")
            return

        treasury_data = treasury_response.json()
        chart_data = treasury_data.get('chart_data', [])
        if not chart_data:
            print("❌ Cannot test yield validation - no chart data")
            return

        # Test with yield far from market rate
        test_point = chart_data[0]
        current_yield = test_point['Yield']
        far_off_yield = current_yield + 5.0  # 5% higher than market

        bad_yield_order = {
            "term": test_point['term'],
            "yield": far_off_yield,
            "quantity": 1000.0
        }

        try:
            response = await client.post(f"{BASE_URL}/orders/", json=bad_yield_order)
            if response.status_code == 400:
                print(f"✅ Yield validation working (rejected {far_off_yield}% vs market {current_yield}%)")
            else:
                print(f"❌ Yield validation failed: {response.status_code}")
                print(f"   Should reject yield {far_off_yield}% when market is {current_yield}%")
        except Exception as e:
            print(f"❌ Error testing yield validation: {e}")

    print("\n🏁 API tests completed!")
    print("\n💡 Key improvements with new approach:")
    print("   • Data transformed once during ingestion, not on every request")
    print("   • Faster API responses (no transformation overhead)")
    print("   • More flexible querying (by date, term, pagination)")
    print("   • Cleaner database schema with proper normalization")
    print("   • Better scalability for large datasets")
    print("\n📋 Orders API Features:")
    print("   • Input validation for all order fields")
    print("   • Market yield validation (prevents unrealistic orders)")
    print("   • Automatic maturity date calculation")
    print("   • Order history with pagination")
    print("   • Complete audit trail with timestamps")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

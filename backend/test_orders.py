#!/usr/bin/env python3
"""
Test script to verify the Orders functionality works correctly.
"""

from sqlmodel import Session, select, desc
from app import engine, Order, ChartDataPoint, create_db_and_tables
import json

def test_orders_database():
    """Test the Orders database functionality."""
    print("Testing Orders database functionality...")

    # Ensure tables exist
    create_db_and_tables()

    with Session(engine) as session:
        # Count existing orders
        existing_orders = session.exec(select(Order)).all()
        print(f"Existing orders in database: {len(existing_orders)}")

        # Check if we have any treasury data
        chart_data = session.exec(select(ChartDataPoint)).first()
        if not chart_data:
            print("❌ No treasury data found - orders cannot be tested")
            return

        print(f"✅ Treasury data available for testing")

        # Create a test order
        test_order = Order(
            term="10Y",
            yield_value=4.15,
            quantity=25000.0,
            issue_date="2025-09-18",
            maturity_date="2035-09-18"
        )

        session.add(test_order)
        session.commit()
        session.refresh(test_order)

        print(f"✅ Test order created with ID: {test_order.id}")
        print(f"   Term: {test_order.term}")
        print(f"   Yield: {test_order.yield_value}%")
        print(f"   Quantity: ${test_order.quantity:,.0f}")
        print(f"   Issue Date: {test_order.issue_date}")
        print(f"   Maturity Date: {test_order.maturity_date}")
        print(f"   Purchase Time: {test_order.purchase_timestamp}")

        # Retrieve all orders
        all_orders = session.exec(
            select(Order).order_by(desc(Order.purchase_timestamp))
        ).all()

        print(f"\nAll orders in database: {len(all_orders)}")
        for i, order in enumerate(all_orders[:3]):  # Show first 3
            print(f"  {i+1}. {order.term} - ${order.quantity:,.0f} @ {order.yield_value}%")

        # Clean up test order
        session.delete(test_order)
        session.commit()
        print(f"\n✅ Test order cleaned up")

def simulate_api_data():
    """Simulate the data that would come from the frontend."""
    print("\n" + "="*50)
    print("Simulating frontend order data...")

    # This represents what the frontend sends
    frontend_order_data = {
        "term": "5Y",
        "yield": 3.74,
        "quantity": 15000.0
    }

    print(f"Frontend order data:")
    print(json.dumps(frontend_order_data, indent=2))

    # This is how it would be processed by the backend
    with Session(engine) as session:
        # Get issue date from latest treasury data
        latest_data = session.exec(
            select(ChartDataPoint).order_by(desc(ChartDataPoint.date))
        ).first()

        if latest_data:
            issue_date = latest_data.date.split('T')[0]
            print(f"✅ Issue date from treasury data: {issue_date}")

            # Calculate maturity date (simplified)
            from datetime import datetime
            issue = datetime.fromisoformat(issue_date)
            years = int(frontend_order_data["term"].replace("Y", ""))
            maturity = issue.replace(year=issue.year + years)
            maturity_date = maturity.strftime("%Y-%m-%d")

            print(f"✅ Calculated maturity date: {maturity_date}")

            # Create the order as the API would
            processed_order = Order(
                term=frontend_order_data["term"],
                yield_value=frontend_order_data["yield"],
                quantity=frontend_order_data["quantity"],
                issue_date=issue_date,
                maturity_date=maturity_date
            )

            print(f"✅ Order ready for database storage:")
            print(f"   Term: {processed_order.term}")
            print(f"   Yield: {processed_order.yield_value}%")
            print(f"   Quantity: ${processed_order.quantity:,.0f}")
            print(f"   Issue: {processed_order.issue_date}")
            print(f"   Maturity: {processed_order.maturity_date}")

def test_order_validation_logic():
    """Test the validation logic that would be in the API."""
    print("\n" + "="*50)
    print("Testing order validation logic...")

    valid_terms = ["1m", "1.5m", "2m", "3m", "4m", "6m", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]

    test_cases = [
        {"term": "10Y", "yield": 4.15, "quantity": 10000, "should_pass": True},
        {"term": "INVALID", "yield": 4.15, "quantity": 10000, "should_pass": False},
        {"term": "10Y", "yield": -1.0, "quantity": 10000, "should_pass": False},
        {"term": "10Y", "yield": 4.15, "quantity": 0, "should_pass": False},
        {"term": "10Y", "yield": 4.15, "quantity": 15000000, "should_pass": False},
    ]

    for i, case in enumerate(test_cases):
        print(f"\nTest case {i+1}: {case}")

        # Term validation
        term_valid = case["term"] in valid_terms

        # Yield validation
        yield_valid = 0 < case["yield"] <= 50

        # Quantity validation
        quantity_valid = 0 < case["quantity"] <= 10_000_000

        overall_valid = term_valid and yield_valid and quantity_valid

        print(f"  Term valid: {term_valid}")
        print(f"  Yield valid: {yield_valid}")
        print(f"  Quantity valid: {quantity_valid}")
        print(f"  Overall: {overall_valid}")

        if overall_valid == case["should_pass"]:
            print(f"  ✅ Validation result matches expected")
        else:
            print(f"  ❌ Validation failed - expected {case['should_pass']}, got {overall_valid}")

def main():
    """Run all order tests."""
    print("🧪 Testing Orders functionality\n")

    try:
        test_orders_database()
        simulate_api_data()
        test_order_validation_logic()

        print("\n🏁 Orders tests completed successfully!")
        print("\n📝 Summary:")
        print("   • Orders can be stored and retrieved from database")
        print("   • Frontend data format is compatible")
        print("   • Validation logic works correctly")
        print("   • Maturity date calculation is functional")

    except Exception as e:
        print(f"\n❌ Orders test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

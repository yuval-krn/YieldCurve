#!/usr/bin/env python3
"""
Test script to verify the SQLite database functionality for treasury chart data.
"""

from sqlmodel import Session, select, desc
from app import engine, ChartDataPoint

def test_database():
    """Test the database by querying records and displaying results."""

    with Session(engine) as session:
        # Count total records
        total_records = len(session.exec(select(ChartDataPoint)).all())
        print(f"Total chart data points in database: {total_records}")

        # Get the latest record
        latest_record = session.exec(
            select(ChartDataPoint).order_by(desc(ChartDataPoint.date))
        ).first()

        if latest_record:
            print(f"\nLatest record:")
            print(f"  ID: {latest_record.id}")
            print(f"  Date: {latest_record.date}")
            print(f"  Term: {latest_record.term}")
            print(f"  Yield: {latest_record.yield_value}%")

        # Get all available dates
        dates = session.exec(
            select(ChartDataPoint.date)
            .distinct()
            .order_by(desc(ChartDataPoint.date))
        ).all()

        print(f"\nAvailable dates: {len(dates)}")
        print(f"Latest date: {dates[0] if dates else 'None'}")
        print(f"Earliest date: {dates[-1] if dates else 'None'}")

        # Get data points for the latest date
        if dates:
            latest_date = dates[0]
            latest_date_points = session.exec(
                select(ChartDataPoint)
                .where(ChartDataPoint.date == latest_date)
                .order_by(ChartDataPoint.term)
            ).all()

            print(f"\nData points for latest date ({latest_date}):")
            for point in latest_date_points:
                print(f"  {point.term:4s}: {point.yield_value}%")

        # Show sample data from first 5 dates
        print(f"\nSample data from first 5 dates:")
        for i, date in enumerate(dates[:5]):
            # Get 10Y yield for this date as an example
            ten_year_point = session.exec(
                select(ChartDataPoint)
                .where(ChartDataPoint.date == date)
                .where(ChartDataPoint.term == "10Y")
            ).first()

            ten_year_yield = ten_year_point.yield_value if ten_year_point else "N/A"
            print(f"  {date}: 10Y = {ten_year_yield}%")

if __name__ == "__main__":
    test_database()

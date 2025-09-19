import httpx
from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
import xml.etree.ElementTree as ET
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select, desc
from typing import Annotated
from datetime import datetime
from pydantic import BaseModel, validator

url = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml"
params = {
    "data": "daily_treasury_yield_curve",
    "field_tdr_date_value": "2025"
}

# Define namespaces (prefixes can be anything, we just map them)
ns = {
    "atom": "http://www.w3.org/2005/Atom",
    "m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
    "d": "http://schemas.microsoft.com/ado/2007/08/dataservices"
}

# SQLModel definitions for transformed chart data
class ChartDataPointBase(SQLModel):
    date: str = Field(index=True)
    term: str = Field(index=True)
    yield_value: float

class ChartDataPoint(ChartDataPointBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

# Orders model
class OrderBase(SQLModel):
    term: str = Field(index=True)
    yield_value: float
    quantity: float
    issue_date: str
    purchase_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    maturity_date: str

class Order(OrderBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

# Pydantic model for order creation (input validation)
class OrderCreate(BaseModel):
    term: str
    quantity: float

    @validator('term')
    def validate_term(cls, v):
        valid_terms = ["1m", "1.5m", "2m", "3m", "4m", "6m", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
        if v not in valid_terms:
            raise ValueError(f'Invalid term. Must be one of: {valid_terms}')
        return v

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0 or v > 10_000_000:  # Max $10M
            raise ValueError('Quantity must be between $1 and $10,000,000')
        return v

# Database setup
sqlite_file_name = "treasury_database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

def transform_and_store_treasury_data(date_value: str, bc_values: dict[str, float | None], session: Session) -> None:
    """Transform raw treasury data and store as individual chart data points"""

    # Human-friendly label mapping
    label_map = {
        "BC_1MONTH": "1m",
        "BC_1_5MONTH": "1.5m",
        "BC_2MONTH": "2m",
        "BC_3MONTH": "3m",
        "BC_4MONTH": "4m",
        "BC_6MONTH": "6m",
        "BC_1YEAR": "1Y",
        "BC_2YEAR": "2Y",
        "BC_3YEAR": "3Y",
        "BC_5YEAR": "5Y",
        "BC_7YEAR": "7Y",
        "BC_10YEAR": "10Y",
        "BC_20YEAR": "20Y",
        "BC_30YEAR": "30Y",
    }

    # Create individual chart data points for each BC field
    for bc_key, yield_value in bc_values.items():
        if bc_key in label_map and yield_value is not None:
            chart_point = ChartDataPoint(
                date=date_value,
                term=label_map[bc_key],
                yield_value=float(yield_value)
            )
            session.add(chart_point)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...creating database tables...")
    create_db_and_tables()

    print("Querying Treasury.gov...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)

    xml_string = response.text
    root = ET.fromstring(xml_string)

    # Store transformed data in database
    with Session(engine) as session:
        # Clear existing data (optional - you might want to keep historical data)
        existing_records = session.exec(select(ChartDataPoint)).all()
        for record in existing_records:
            session.delete(record)
        session.commit()

        # Iterate over all <entry> elements and transform data during ingestion
        for entry in root.findall("atom:entry", ns):
            content = entry.find("atom:content", ns)
            if content is not None:
                props = content.find("m:properties", ns)
                if props is not None:
                    # Extract the date
                    date_elem = props.find("d:NEW_DATE", ns)
                    date_value = date_elem.text if date_elem is not None else None

                    if date_value:
                        # Extract all BC_ values dynamically
                        bc_values: dict[str, float | None] = {}
                        for child in props:
                            if child.tag.startswith("{%s}BC_" % ns["d"]):
                                # strip namespace
                                bc_name = child.tag.split("}", 1)[1]
                                bc_values[bc_name] = float(str(child.text)) if child.text else None

                        # Transform and store the data
                        transform_and_store_treasury_data(date_value, bc_values, session)

        session.commit()

        # Print first record as example
        first_record = session.exec(select(ChartDataPoint)).first()
        if first_record:
            print(f"First chart data point: {first_record.date} - {first_record.term}: {first_record.yield_value}%")

        # Count total chart data points
        total_points = len(session.exec(select(ChartDataPoint)).all())
        print(f"Total chart data points stored: {total_points}")

    yield

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def read_root(session: SessionDep):
    # Get the latest date from the chart data
    latest_date_record = session.exec(
        select(ChartDataPoint).order_by(desc(ChartDataPoint.date))
    ).first()

    if not latest_date_record:
        return {"error": "No treasury data found"}

    latest_date = latest_date_record.date

    # Get all chart data points for the latest date
    chart_data_points = session.exec(
        select(ChartDataPoint).where(ChartDataPoint.date == latest_date)
    ).all()

    if not chart_data_points:
        return {"error": "No chart data found for latest date"}

    # Convert to the expected format
    chart_data: list[dict[str, str | float]] = []
    for point in chart_data_points:
        chart_data.append({
            "term": point.term,
            "Yield": point.yield_value
        })

    # Sort chart data in logical order
    order = ["1m", "1.5m", "2m", "3m", "4m", "6m", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
    chart_data.sort(key=lambda x: order.index(x["term"]) if x["term"] in order else 999)

    return {
        "date": latest_date,
        "chart_data": chart_data
    }

@app.get("/treasury/dates/")
def read_available_dates(session: SessionDep):
    """Get all available dates"""
    dates = session.exec(
        select(ChartDataPoint.date)
        .distinct()
        .order_by(desc(ChartDataPoint.date))
    ).all()
    return {"dates": dates}

@app.get("/treasury/{date}")
def read_treasury_by_date(date: str, session: SessionDep):
    """Get chart data for a specific date"""
    chart_data_points = session.exec(
        select(ChartDataPoint).where(ChartDataPoint.date == date)
    ).all()

    if not chart_data_points:
        raise HTTPException(status_code=404, detail="No data found for specified date")

    # Convert to the expected format
    chart_data: list[dict[str, str | float]] = []
    for point in chart_data_points:
        chart_data.append({
            "term": point.term,
            "Yield": point.yield_value
        })

    # Sort chart data in logical order
    order = ["1m", "1.5m", "2m", "3m", "4m", "6m", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
    chart_data.sort(key=lambda x: order.index(x["term"]) if x["term"] in order else 999)

    return {
        "date": date,
        "chart_data": chart_data
    }

@app.get("/treasury/", response_model=list[ChartDataPointBase])
def read_all_chart_data(
    session: SessionDep,
    offset: int = 0,
    limit: int = 100,
):
    """Get all chart data points with pagination"""
    chart_data_points = session.exec(
        select(ChartDataPoint)
        .order_by(desc(ChartDataPoint.date), ChartDataPoint.term)
        .offset(offset)
        .limit(limit)
    ).all()
    return chart_data_points

# Helper function to calculate maturity date
def calculate_maturity_date(issue_date: str, term: str) -> str:
    """Calculate maturity date based on issue date and term"""
    from datetime import datetime, timedelta

    issue = datetime.fromisoformat(issue_date.replace('T00:00:00', ''))

    if term.endswith("m"):
        # Month terms like "1m", "6m", "1.5m"
        months = float(term.replace("m", ""))
        # Approximate months as 30 days for simplicity
        days = int(months * 30)
        maturity = issue + timedelta(days=days)
    elif term.endswith("Y"):
        # Year terms like "1Y", "2Y", "30Y"
        years = int(term.replace("Y", ""))
        maturity = issue.replace(year=issue.year + years)
    else:
        # Default to 1 year if unknown format
        maturity = issue.replace(year=issue.year + 1)

    return maturity.strftime("%Y-%m-%d")

@app.post("/orders/", response_model=Order)
def create_order(order_data: OrderCreate, session: SessionDep):
    """Create a new order with input validation"""

    # Validate that the term exists in our current treasury data
    latest_date_record = session.exec(
        select(ChartDataPoint).order_by(desc(ChartDataPoint.date))
    ).first()

    if not latest_date_record:
        raise HTTPException(status_code=400, detail="No treasury data available")

    # Check if the term exists in current data
    term_exists = session.exec(
        select(ChartDataPoint)
        .where(ChartDataPoint.date == latest_date_record.date)
        .where(ChartDataPoint.term == order_data.term)
    ).first()

    if not term_exists:
        raise HTTPException(
            status_code=400,
            detail=f"Term '{order_data.term}' not available in current treasury data"
        )

    # Use the current market yield for this term
    current_yield = term_exists.yield_value

    # Create the order
    issue_date = latest_date_record.date.split('T')[0]  # Extract date part
    maturity_date = calculate_maturity_date(issue_date, order_data.term)

    db_order = Order(
        term=order_data.term,
        yield_value=current_yield,
        quantity=order_data.quantity,
        issue_date=issue_date,
        maturity_date=maturity_date
    )

    session.add(db_order)
    session.commit()
    session.refresh(db_order)

    return db_order

@app.get("/orders/", response_model=list[Order])
def get_orders(
    session: SessionDep,
    offset: int = 0,
    limit: int = 100,
):
    """Get all orders with pagination, ordered by most recent first"""
    orders = session.exec(
        select(Order)
        .order_by(desc(Order.purchase_timestamp))
        .offset(offset)
        .limit(limit)
    ).all()
    return orders

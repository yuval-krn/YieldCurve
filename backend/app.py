import httpx
from fastapi import FastAPI
from contextlib import asynccontextmanager
import xml.etree.ElementTree as ET
from fastapi.middleware.cors import CORSMiddleware
from typing import Union

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

data_list = []

def transform_treasury_data(data: dict[str, str | float | None]]) -> list[dict[str, str | float]]:
    """Transform raw treasury data into chart-friendly format"""

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

    # Filter out non-BC keys and transform to chart points
    chart_data = []
    for key, value in data.items():
        if key != "date" and "DISPLAY" not in key and key.startswith("BC_"):
            chart_data.append({
                "term": label_map.get(key, key),
                "Yield": float(value) if value is not None else 0.0
            })

    # Sort maturities in logical order
    order = ["1m", "1.5m", "2m", "3m", "4m", "6m", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
    chart_data.sort(key=lambda x: order.index(x["term"]) if x["term"] in order else 999)

    return chart_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...queuerying Treasury.gov...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)

    xml_string = response.text
    root = ET.fromstring(xml_string)


    # Iterate over all <entry> elements
    for entry in root.findall("atom:entry", ns):
        content = entry.find("atom:content", ns)
        if content is not None:
            props = content.find("m:properties", ns)
            if props is not None:
                # Extract the date
                date_elem = props.find("d:NEW_DATE", ns)
                date_value = date_elem.text if date_elem is not None else None

                # Extract all BC_ values dynamically
                bc_values = {}
                for child in props:
                    if child.tag.startswith("{%s}BC_" % ns["d"]):
                        # strip namespace
                        bc_name = child.tag.split("}", 1)[1]
                        bc_values[bc_name] = float(str(child.text))

                # Combine into a single dictionary for this entry
                row: dict[str, Union[str, float, None]] = {"date": date_value, **bc_values}
                data_list.append(row)

    # Example: print first row
    print(data_list[0])
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
def read_root():
    raw_data = data_list[-1]
    transformed_data = transform_treasury_data(raw_data)
    return {
        "date": raw_data["date"],
        "chart_data": transformed_data
    }

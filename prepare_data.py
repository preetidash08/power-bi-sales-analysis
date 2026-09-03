"""
Loads the Sales_Star_Schema.xlsx workbook and merges the fact + dimension
tables into one flat table for the dashboard.
"""
import pandas as pd

SOURCE_FILE = "Sales_Star_Schema.xlsx"

def load_merged_sales():
    xls = pd.ExcelFile(SOURCE_FILE)

    fact = pd.read_excel(xls, "Fact_Sales")
    customers = pd.read_excel(xls, "Dim_Customer")
    reps = pd.read_excel(xls, "Dim_Rep")
    products = pd.read_excel(xls, "Dim_Product")

    df = (
        fact
        .merge(customers, on="Customer_ID", how="left")
        .merge(reps, on="Sales_Rep_ID", how="left", suffixes=("", "_Rep"))
        .merge(products, on="Product_Key", how="left")
    )

    # Rep dimension also has a "Region" column (rep's home region) which
    # collides with the customer's region — keep both, clearly named.
    df = df.rename(columns={"Region": "Customer_Region", "Region_Rep": "Rep_Region"})

    return df


def load_targets():
    xls = pd.ExcelFile(SOURCE_FILE)
    targets = pd.read_excel(xls, "Fact_Targets")
    reps = pd.read_excel(xls, "Dim_Rep")
    return targets.merge(reps, on="Sales_Rep_ID", how="left")


# Approximate lat/lon for the 20 cities present in Dim_Customer
CITY_COORDS = {
    "Ahmedabad": (23.0225, 72.5714), "Bengaluru": (12.9716, 77.5946),
    "Bhubaneswar": (20.2961, 85.8245), "Chennai": (13.0827, 80.2707),
    "Gurugram": (28.4595, 77.0266), "Guwahati": (26.1445, 91.7362),
    "Hyderabad": (17.3850, 78.4867), "Indore": (22.7196, 75.8577),
    "Jaipur": (26.9124, 75.7873), "Kochi": (9.9312, 76.2673),
    "Kolkata": (22.5726, 88.3639), "Ludhiana": (30.9010, 75.8573),
    "Mumbai": (19.0760, 72.8777), "New Delhi": (28.6139, 77.2090),
    "Noida": (28.5355, 77.3910), "Panaji": (15.4909, 73.8278),
    "Patna": (25.5941, 85.1376), "Pune": (18.5204, 73.8567),
    "Ranchi": (23.3441, 85.3096), "Visakhapatnam": (17.6868, 83.2185),
}


if __name__ == "__main__":
    df = load_merged_sales()
    df["Lat"] = df["City"].map(lambda c: CITY_COORDS.get(c, (None, None))[0])
    df["Lon"] = df["City"].map(lambda c: CITY_COORDS.get(c, (None, None))[1])
    df.to_csv("sales_data.csv", index=False)
    print(f"Merged {len(df)} sales rows -> sales_data.csv")
    print(df.columns.tolist())

    targets = load_targets()
    targets.to_csv("targets_data.csv", index=False)
    print(f"Merged {len(targets)} target rows -> targets_data.csv")

import pandas as pd
import re

from sqlalchemy import create_engine, text
from config import MYSQL_CONFIG

# =====================================================
# MYSQL CONNECTION
# =====================================================

db_url = (
    f"mysql+pymysql://{MYSQL_CONFIG['user']}:"
    f"{MYSQL_CONFIG['password']}@"
    f"{MYSQL_CONFIG['host']}:"
    f"{MYSQL_CONFIG['port']}/"
    f"{MYSQL_CONFIG['database']}"
)

engine = create_engine(db_url)

print("Connected to MySQL!")


# =====================================================
# LOAD CSV FILES
# =====================================================

flights_df = pd.read_csv(
    r"data/airline_delay.csv"
)

states_df = pd.read_csv(
    r"data/states.csv"
)

print("CSV files loaded!")

# =====================================================
# LOWERCASE FLIGHT COLUMNS
# =====================================================

flights_df.columns = flights_df.columns.str.lower()

# =====================================================
# RENAME STATES COLUMNS
# =====================================================

states_df.columns = [
    "state_name",
    "state_code",
    "region",
    "division"
]

# =====================================================
# EXTRACT STATE CODE
# =====================================================

def extract_state_code(airport_name):

    try:

        match = re.search(
            r',\s([A-Z]{2})\:',
            str(airport_name)
        )

        if match:
            return match.group(1)

    except:
        return None

    return None


flights_df["state_code"] = flights_df[
    "airport_name"
].apply(extract_state_code)

print("State code extracted!")

# =====================================================
# INSERT REGIONS
# =====================================================

regions_df = states_df[
    ["region"]
].drop_duplicates()

regions_df.columns = ["region_name"]

regions_df = regions_df.drop_duplicates(
    subset=["region_name"]
)

regions_df.to_sql(
    "regions",
    con=engine,
    if_exists="append",
    index=False
)

print("Regions inserted!")

# =====================================================
# GET REGION LOOKUP
# =====================================================

region_lookup = pd.read_sql(
    "SELECT * FROM regions",
    engine
)

# =====================================================
# MERGE STATES WITH REGION_ID
# =====================================================

states_df = states_df.merge(
    region_lookup,
    left_on="region",
    right_on="region_name"
)

# =====================================================
# INSERT STATES
# =====================================================

states_insert = states_df[
    [
        "state_code",
        "state_name",
        "region_id"
    ]
]

states_insert = states_insert.drop_duplicates(
    subset=["state_code"]
)

states_insert.to_sql(
    "states",
    con=engine,
    if_exists="append",
    index=False
)

print("States inserted!")

# =====================================================
# INSERT AIRLINES
# =====================================================

airlines_df = flights_df[
    [
        "carrier",
        "carrier_name"
    ]
].copy()

airlines_df = airlines_df.drop_duplicates(
    subset=["carrier"]
)

airlines_df.to_sql(
    "airlines",
    con=engine,
    if_exists="append",
    index=False
)

print("Airlines inserted!")

# =====================================================
# INSERT AIRPORTS
# =====================================================

airports_df = flights_df[
    [
        "airport",
        "airport_name",
        "state_code"
    ]
].copy()

# hapus duplicate airport
airports_df = airports_df.drop_duplicates(
    subset=["airport"]
)

# ambil hanya state_code valid
valid_states = states_insert["state_code"].unique()

airports_df = airports_df[
    airports_df["state_code"].isin(valid_states)
]

# hapus state_code null
airports_df = airports_df.dropna(
    subset=["state_code"]
)

airports_df.to_sql(
    "airports",
    con=engine,
    if_exists="append",
    index=False
)

print("Airports inserted!")

# =====================================================
# GET AIRLINE LOOKUP
# =====================================================

airline_lookup = pd.read_sql(
    "SELECT * FROM airlines",
    engine
)

# =====================================================
# GET AIRPORT LOOKUP
# =====================================================

airport_lookup = pd.read_sql(
    "SELECT * FROM airports",
    engine
)

# =====================================================
# MERGE carrier_id
# =====================================================

flights_df = flights_df.merge(
    airline_lookup[
        ["carrier_id", "carrier"]
    ],
    on="carrier",
    how="left"
)

# hapus yang carrier_id tidak ketemu
flights_df = flights_df.dropna(
    subset=["carrier_id"]
)

# ubah ke integer
flights_df["carrier_id"] = (
    flights_df["carrier_id"]
    .astype(int)
)

# =====================================================
# MERGE airport_id
# =====================================================

flights_df = flights_df.merge(
    airport_lookup[
        ["airport_id", "airport"]
    ],
    on="airport",
    how="left"
)

# hapus yang airport_id tidak ketemu
flights_df = flights_df.dropna(
    subset=["airport_id"]
)

# ubah ke integer
flights_df["airport_id"] = (
    flights_df["airport_id"]
    .astype(int)
)

# =====================================================
# FINAL FLIGHTS TABLE
# =====================================================

flights_insert = flights_df[
    [
        "year",
        "month",

        "carrier_id",
        "airport_id",

        "arr_flights",
        "arr_del15",
        "arr_cancelled",
        "arr_diverted",

        "arr_delay",

        "carrier_ct",
        "weather_ct",
        "nas_ct",
        "security_ct",
        "late_aircraft_ct",

        "carrier_delay",
        "weather_delay",
        "nas_delay",
        "security_delay",
        "late_aircraft_delay"
    ]
]

# =====================================================
# HANDLE NULL
# =====================================================

numeric_cols = [
    "arr_flights",
    "arr_del15",
    "arr_cancelled",
    "arr_diverted",
    "arr_delay",
    "carrier_ct",
    "weather_ct",
    "nas_ct",
    "security_ct",
    "late_aircraft_ct",
    "carrier_delay",
    "weather_delay",
    "nas_delay",
    "security_delay",
    "late_aircraft_delay"
]

flights_insert[numeric_cols] = (
    flights_insert[numeric_cols]
    .fillna(0)
)


# =====================================================
# INSERT FLIGHTS
# =====================================================

flights_insert.to_sql(
    "flights",
    con=engine,
    if_exists="append",
    index=False,
    chunksize=1000
)

print("Flights inserted!")


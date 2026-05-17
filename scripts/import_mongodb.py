import pandas as pd
from sqlalchemy import create_engine
from pymongo import MongoClient
from config import MYSQL_CONFIG, MONGO_CONFIG

# =====================================================
# CONNECT MYSQL
# =====================================================
engine = create_engine(
    f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}"
    f"@{MYSQL_CONFIG['host']}/{MYSQL_CONFIG['database']}"
)

print("Connected to MySQL!")

# =====================================================
# CONNECT MONGODB
# =====================================================
client = MongoClient(MONGO_CONFIG["uri"])
db = client[MONGO_CONFIG["database"]]

print("Connected to MongoDB!")

# =====================================================
# LOAD DATA FROM MYSQL
# =====================================================
flights = pd.read_sql("SELECT * FROM flights", engine)
airports = pd.read_sql("SELECT * FROM airports", engine)
states = pd.read_sql("SELECT * FROM states", engine)
regions = pd.read_sql("SELECT * FROM regions", engine)
airlines = pd.read_sql("SELECT * FROM airlines", engine)

print("Data loaded from MySQL!")

# lowercase columns biar aman
for df in [flights, airports, states, regions, airlines]:
    df.columns = df.columns.str.lower()

# =====================================================
# JOIN DIMENSION 
# =====================================================

# airports → states
airports_states = airports.merge(states, on="state_code", how="left")

# states → regions
airports_states = airports_states.merge(regions, on="region_id", how="left")

# flights → airports_states
flights = flights.merge(
    airports_states[["airport_id", "state_code", "region_name"]],
    on="airport_id",
    how="left"
)

# flights → airlines
flights = flights.merge(
    airlines[["carrier_id", "carrier", "carrier_name"]],
    on="carrier_id",
    how="left"
)

flights.rename(columns={"region_name": "region"}, inplace=True)

flights = flights.fillna(0)

print("JOIN completed!")

# =====================================================
# 1. delay_time_analysis
# =====================================================
delay_time = flights.groupby(["year", "month", "region"]).agg(
    total_flights=("arr_flights", "sum"),
    total_delay_flights=("arr_del15", "sum"),
    weather_delay_count=("weather_ct", "sum"),
    weather_delay_duration=("weather_delay", "sum")
).reset_index()

delay_time["weather_delay_percentage_total"] = (
    delay_time["weather_delay_count"] /
    delay_time["total_flights"].replace(0, 1) * 100
)

delay_time["weather_risk_share"] = (
    delay_time["weather_delay_count"] /
    delay_time["total_delay_flights"].replace(0, 1) * 100
)

delay_time["avg_delay"] = (
    delay_time["weather_delay_duration"] /
    delay_time["weather_delay_count"].replace(0, 1)
)

# =====================================================
# RISK LEVEL 
# =====================================================
q_low = delay_time["weather_delay_percentage_total"].quantile(0.33)
q_high = delay_time["weather_delay_percentage_total"].quantile(0.66)

def classify_risk(x):
    if x <= q_low:
        return "Low"
    elif x <= q_high:
        return "Medium"
    return "High"

delay_time["risk_level"] = delay_time["weather_delay_percentage_total"].apply(classify_risk)

db.delay_time_analysis.delete_many({})
db.delay_time_analysis.insert_many(delay_time.to_dict("records"))

print("Inserted delay_time_analysis")

# =====================================================
# 2. airline_performance
# =====================================================
airline_perf = flights.groupby(
    ["year", "month", "carrier", "carrier_name"]
).agg(
    total_flights=("arr_flights", "sum"),
    total_delay_flights=("arr_del15", "sum"),
    avg_delay=("arr_delay", "mean")
).reset_index()

airline_perf["delay_percentage"] = (
    airline_perf["total_delay_flights"] /
    airline_perf["total_flights"].replace(0, 1) * 100
)

airline_perf["rank"] = airline_perf.groupby(
    ["year", "month"]
)["delay_percentage"].rank(method="dense", ascending=True)

db.airline_performance.delete_many({})
db.airline_performance.insert_many(airline_perf.to_dict("records"))

print("Inserted airline_performance")

# =====================================================
# 3. delay_cause_distribution
# =====================================================
delay_cause = flights.groupby(["year", "month", "region"]).agg(
    carrier_ct=("carrier_ct", "sum"),
    weather_ct=("weather_ct", "sum"),
    nas_ct=("nas_ct", "sum"),
    security_ct=("security_ct", "sum"),
    late_aircraft_ct=("late_aircraft_ct", "sum")
).reset_index()

ct_cols = ["carrier_ct","weather_ct","nas_ct","security_ct","late_aircraft_ct"]

delay_cause["dominant_by_ct"] = delay_cause[ct_cols].idxmax(axis=1)

db.delay_cause_distribution.delete_many({})
db.delay_cause_distribution.insert_many(delay_cause.to_dict("records"))

print("Inserted delay_cause_distribution")

print("===================================")
print("ALL MONGODB DATA SUCCESSFULLY IMPORTED")
print("===================================")
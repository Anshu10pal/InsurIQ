"""
Ordinal encoding maps — converts string range values to numeric midpoints.
Derived from EDA findings on fraud_oracle.csv.
"""

DAYS_POLICY_ACCIDENT_MAP = {"none": 0, "1 to 7": 4, "8 to 15": 11, "15 to 30": 22, "more than 30": 45}
DAYS_POLICY_CLAIM_MAP = {"none": 0, "1 to 7": 4, "8 to 15": 11, "15 to 30": 22, "more than 30": 45}
PAST_NUMBER_OF_CLAIMS_MAP = {"none": 0, "1": 1, "2 to 4": 3, "more than 4": 5}
AGE_OF_VEHICLE_MAP = {"new": 0, "2 years": 2, "3 years": 3, "4 years": 4, "5 years": 5, "6 years": 6, "7 years": 7, "more than 7": 9}
AGE_OF_POLICY_HOLDER_MAP = {"16 to 17": 16, "18 to 20": 19, "21 to 25": 23, "26 to 30": 28, "31 to 35": 33, "36 to 40": 38, "41 to 50": 45, "51 to 65": 58, "over 65": 70}
VEHICLE_PRICE_MAP = {"less than 20000": 15000, "20000 to 29000": 24500, "30000 to 39000": 34500, "40000 to 59000": 49500, "60000 to 69000": 64500, "more than 69000": 80000}
NUMBER_OF_SUPPLIMENTS_MAP = {"none": 0, "1 to 2": 1, "3 to 5": 4, "more than 5": 6}
ADDRESS_CHANGE_CLAIM_MAP = {"no change": 0, "under 6 months": 0, "1 year": 1, "2 to 3 years": 2, "4 to 8 years": 6}
NUMBER_OF_CARS_MAP = {"1 vehicle": 1, "2 vehicles": 2, "3 to 4": 3, "more than 4": 5}

ALL_ORDINAL_MAPS = {
    "Days_Policy_Accident": DAYS_POLICY_ACCIDENT_MAP,
    "Days_Policy_Claim": DAYS_POLICY_CLAIM_MAP,
    "PastNumberOfClaims": PAST_NUMBER_OF_CLAIMS_MAP,
    "AgeOfVehicle": AGE_OF_VEHICLE_MAP,
    "AgeOfPolicyHolder": AGE_OF_POLICY_HOLDER_MAP,
    "VehiclePrice": VEHICLE_PRICE_MAP,
    "NumberOfSuppliments": NUMBER_OF_SUPPLIMENTS_MAP,
    "NumberOfSupplements": NUMBER_OF_SUPPLIMENTS_MAP,  # alias for renamed column
    "AddressChange_Claim": ADDRESS_CHANGE_CLAIM_MAP,
    "NumberOfCars": NUMBER_OF_CARS_MAP,
}


def encode_ordinal(column_name: str, value: str, default: float = 0.0) -> float:
    if column_name not in ALL_ORDINAL_MAPS:
        return default
    mapping = ALL_ORDINAL_MAPS[column_name]
    if value is None:
        return default
    normalized = str(value).strip().lower()
    for key, numeric in mapping.items():
        if key.lower() == normalized:
            return float(numeric)
    return default


def encode_all_ordinals(row: dict) -> dict:
    encoded = row.copy()
    column_map = {
        "Days_Policy_Accident": "days_policy_accident_numeric",
        "Days_Policy_Claim": "days_policy_claim_numeric",
        "PastNumberOfClaims": "past_claims_numeric",
        "AgeOfVehicle": "age_of_vehicle_numeric",
        "AgeOfPolicyHolder": "age_of_policy_holder_numeric",
        "VehiclePrice": "vehicle_price_numeric",
        "NumberOfSuppliments": "supplements_numeric",
        "AddressChange_Claim": "address_change_numeric",
        "NumberOfCars": "number_of_cars_numeric",
    }
    for csv_col, numeric_col in column_map.items():
        raw_value = row.get(csv_col, "")
        encoded[numeric_col] = encode_ordinal(csv_col, raw_value)
    return encoded

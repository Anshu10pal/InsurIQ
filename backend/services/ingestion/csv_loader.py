"""
CSV loader — reads fraud_oracle_cleaned.csv, validates schema, encodes ordinal fields.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from utils.logging import get_logger
from services.ingestion.ordinal_maps import encode_all_ordinals

logger = get_logger(__name__)

EXPECTED_COLUMNS = [
    "Month", "WeekOfMonth", "DayOfWeek", "Make", "AccidentArea",
    "DayOfWeekClaimed", "MonthClaimed", "WeekOfMonthClaimed", "Sex",
    "MaritalStatus", "Age", "Fault", "PolicyType", "VehicleCategory",
    "VehiclePrice", "FraudFound_P", "PolicyNumber", "RepNumber",
    "Deductible", "DriverRating", "Days_Policy_Accident", "Days_Policy_Claim",
    "PastNumberOfClaims", "AgeOfVehicle", "AgeOfPolicyHolder",
    "PoliceReportFiled", "WitnessPresent", "AgentType",
    "NumberOfSupplements", "AddressChange_Claim", "NumberOfCars",
    "Year", "BasePolicy",
]
REQUIRED_COLUMNS = ["PolicyNumber", "FraudFound_P", "AccidentArea", "VehicleCategory"]


def load_and_validate_csv(file_path: str) -> pd.DataFrame:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at: {file_path}")
    logger.info("loading_csv", path=str(path))
    df = pd.read_csv(path)
    # Support both old and new spelling
    if "NumberOfSuppliments" in df.columns and "NumberOfSupplements" not in df.columns:
        df = df.rename(columns={"NumberOfSuppliments": "NumberOfSupplements"})
    missing_cols = set(EXPECTED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing expected columns: {missing_cols}")
    logger.info("csv_loaded", rows=len(df), columns=len(df.columns))
    df = df.replace({np.nan: None})
    object_cols = df.select_dtypes(include="object").columns
    for col in object_cols:
        df[col] = df[col].astype(str).str.strip()
    fraud_count = df["FraudFound_P"].sum()
    total = len(df)
    logger.info("class_distribution", total=total, fraud=int(fraud_count),
                non_fraud=int(total - fraud_count), fraud_rate=f"{fraud_count/total*100:.2f}%")
    return df


def df_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    df = df.replace({np.nan: None})
    records = df.to_dict(orient="records")
    encoded_records = [encode_all_ordinals(r) for r in records]
    logger.info("records_prepared", count=len(encoded_records))
    return encoded_records

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def load_water_data() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "water_usage.csv")
    df = pd.read_csv(path)
    df["anomaly"] = df["anomaly"].astype(str).str.lower().map({"true": True, "false": False})
    return df


def load_energy_data() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "energy_usage.csv")
    df = pd.read_csv(path)
    df["anomaly"] = df["anomaly"].astype(str).str.lower().map({"true": True, "false": False})
    return df


def load_waste_kb() -> dict:
    import json
    path = os.path.join(DATA_DIR, "waste_knowledge_base.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

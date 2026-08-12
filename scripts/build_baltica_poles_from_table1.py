#!/usr/bin/env python3
"""
Build data/Baltica_poles.csv from the manuscript/source Table 1 Excel file.

Input expected in the repository:
    data/Table1_Salminen_etal_2027.xlsx

Output generated for the webpage:
    data/Baltica_poles.csv

This file is used by the pole compilation page, interactive map, and
pole-assessment pages. It keeps the webpage table synchronized with Table 1.
"""

from __future__ import annotations

import csv
import math
import re
from pathlib import Path
from typing import Iterable

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
INPUT_XLSX = DATA_DIR / "Table1_Salminen_etal_2027.xlsx"
OUTPUT_CSV = DATA_DIR / "Baltica_poles.csv"

SHEET_CANDIDATES = ["Table 1", "Table1", "table 1", "Sheet1"]

OUTPUT_COLUMNS = [
    "Terrane",
    "Unit",
    "Age_Ma",
    "age_min",
    "age_max",
    "Rating",
    "S_LONG",
    "S_LAT",
    "P_LONG",
    "P_LAT",
    "A95",
    "Reference",
]

KEEP_GRADES = {"A", "B", "C+"}


def clean_text(value: object) -> str:
    """Return a safe, single-line text string."""
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "<na>"}:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text


def clean_number(value: object) -> float | None:
    """Convert a table cell to a float, accepting decimal commas and stray spaces."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)
    text = clean_text(value)
    if text == "":
        return None
    text = text.replace(",", ".")
    text = re.sub(r"[^0-9.+\-eE]", "", text)
    if text in {"", "+", "-", "."}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def fmt_number(value: float | None) -> str:
    """Format numeric values compactly for the CSV."""
    if value is None:
        return ""
    if abs(value - round(value)) < 1e-10:
        return str(int(round(value)))
    return (f"{value:.10g}").rstrip("0").rstrip(".")


def normalize_header(value: object) -> str:
    text = clean_text(value).lower()
    text = text.replace("˚", "°")
    text = text.replace("_", " ")
    text = re.sub(r"[^a-z0-9°+#]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_grade(value: object) -> str:
    grade = clean_text(value).upper().replace(" ", "")
    grade = grade.replace("−", "-")
    if grade.startswith("A"):
        return "A"
    if grade.startswith("B"):
        return "B"
    if grade.startswith("C") and "D" not in grade:
        return "C+"
    if grade == "D" or "D" in grade:
        return "D"
    return ""


def find_header_row(raw: pd.DataFrame) -> int:
    """Find the row containing Table 1 column headers."""
    max_rows = min(20, len(raw))
    for i in range(max_rows):
        row = [normalize_header(x) for x in raw.iloc[i].tolist()]
        has_terrane = "terrane" in row
        has_rock = any(x in row for x in ["rockname", "rock name", "unit"])
        has_age = any("nominal age" in x or x == "age" or x == "age ma" for x in row)
        has_pole = any(x in row for x in ["plat", "plong", "clat", "clong"])
        if has_terrane and has_rock and has_age and has_pole:
            return i
    raise RuntimeError("Could not detect the Table 1 header row. Check the Excel file/header names.")


def pick_column(columns: Iterable[str], candidates: list[str], required: bool = True) -> str | None:
    """Find a dataframe column by normalized candidate names."""
    normalized = {normalize_header(c): c for c in columns}
    for cand in candidates:
        key = normalize_header(cand)
        if key in normalized:
            return normalized[key]
    if required:
        raise RuntimeError(
            "Missing required column. Tried: "
            + ", ".join(candidates)
            + ". Available columns: "
            + ", ".join(map(str, columns))
        )
    return None


def read_table1() -> pd.DataFrame:
    if not INPUT_XLSX.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_XLSX}\n"
            "Upload/rename the source Table 1 file to data/Table1_Salminen_etal_2027.xlsx"
        )

    xls = pd.ExcelFile(INPUT_XLSX)
    sheet_name = next((s for s in SHEET_CANDIDATES if s in xls.sheet_names), xls.sheet_names[0])

    raw = pd.read_excel(INPUT_XLSX, sheet_name=sheet_name, header=None, dtype=object)
    header_idx = find_header_row(raw)
    header = [clean_text(x) for x in raw.iloc[header_idx].tolist()]
    df = raw.iloc[header_idx + 1 :].copy()
    df.columns = header
    df = df.dropna(how="all")
    df = df.loc[:, [c for c in df.columns if clean_text(c) != ""]]

    print(f"Read {INPUT_XLSX.name}, sheet '{sheet_name}', header row {header_idx + 1}")
    print(f"Rows after removing empty rows: {len(df)}")
    return df


def build_baltica_poles(df: pd.DataFrame) -> pd.DataFrame:
    cols = list(df.columns)

    c_terrane = pick_column(cols, ["Terrane", "Block", "Craton"])
    c_unit = pick_column(cols, ["ROCKNAME", "Rock name", "Unit"])
    c_age = pick_column(cols, ["nominal age", "Age nominal", "Age_Ma", "Age Ma", "Age"])
    c_age_low = pick_column(cols, ["lomagage", "lowmagage", "Age low", "age_min", "young age"], required=False)
    c_age_high = pick_column(cols, ["himagage", "highmagage", "Age high", "age_max", "old age"], required=False)
    c_grade = pick_column(cols, ["Grade", "Rating"])
    c_slon = pick_column(cols, ["S_LONG", "SLONG", "SLONG°E", "site lon", "site longitude"])
    c_slat = pick_column(cols, ["S_LAT", "SLAT", "SLAT°N", "site lat", "site latitude"])

    # Use corrected pole coordinates if Table 1 has them; otherwise use PLAT/PLONG.
    c_plat = pick_column(cols, ["Clat", "CLAT", "Corrected lat", "Corrected latitude"], required=False)
    c_plon = pick_column(cols, ["Clong", "CLONG", "Corrected long", "Corrected longitude"], required=False)
    c_plat_orig = pick_column(cols, ["PLAT", "Plat", "P_LAT", "Pole latitude"])
    c_plon_orig = pick_column(cols, ["PLONG", "Plong", "P_LONG", "Pole longitude"])

    c_a95 = pick_column(cols, ["A95", "a95", "Alpha95", "alpha95"])
    c_ref = pick_column(cols, ["Pole ref", "Reference", "References", "Authors"], required=False)

    rows: list[dict[str, str]] = []
    for _, r in df.iterrows():
        terrane = clean_text(r[c_terrane])
        unit = clean_text(r[c_unit])
        rating = normalize_grade(r[c_grade])

        if rating not in KEEP_GRADES:
            continue

        age = clean_number(r[c_age])
        if age is None:
            continue

        age_low = clean_number(r[c_age_low]) if c_age_low else None
        age_high = clean_number(r[c_age_high]) if c_age_high else None
        age_values = [x for x in [age_low, age_high] if x is not None]
        age_min = min(age_values) if age_values else age
        age_max = max(age_values) if age_values else age

        s_lon = clean_number(r[c_slon])
        s_lat = clean_number(r[c_slat])

        p_lat = clean_number(r[c_plat]) if c_plat else None
        p_lon = clean_number(r[c_plon]) if c_plon else None
        if p_lat is None:
            p_lat = clean_number(r[c_plat_orig])
        if p_lon is None:
            p_lon = clean_number(r[c_plon_orig])
        if p_lon is not None:
            p_lon = p_lon % 360

        a95 = clean_number(r[c_a95])
        ref = clean_text(r[c_ref]) if c_ref else ""

        if not terrane or not unit or s_lon is None or s_lat is None or p_lon is None or p_lat is None or a95 is None:
            # Skip incomplete rows because they cannot be mapped/rebuilt reliably.
            continue

        rows.append(
            {
                "Terrane": terrane,
                "Unit": unit,
                "Age_Ma": fmt_number(age),
                "age_min": fmt_number(age_min),
                "age_max": fmt_number(age_max),
                "Rating": rating,
                "S_LONG": fmt_number(s_lon),
                "S_LAT": fmt_number(s_lat),
                "P_LONG": fmt_number(p_lon),
                "P_LAT": fmt_number(p_lat),
                "A95": fmt_number(a95),
                "Reference": ref,
            }
        )

    out = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
out["_sort_age"] = pd.to_numeric(out["Age_Ma"], errors="coerce")
out = out.sort_values(["_sort_age", "Terrane", "Unit"])
out = out.drop(columns=["_sort_age"])
    return out


def main() -> None:
    df = read_table1()
    out = build_baltica_poles(df)

    if out.empty:
        raise RuntimeError("No A/B/C+ poles were exported. Check Grade/coordinate columns in Table 1.")

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT_CSV, sep=";", index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)

    print(f"Saved {len(out)} poles to {OUTPUT_CSV}")
    print("Grade counts:")
    print(out["Rating"].value_counts().to_string())


if __name__ == "__main__":
    main()

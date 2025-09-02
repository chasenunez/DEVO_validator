#!/usr/bin/env python3
import sys
import csv
import json
import os
from frictionless import Resource

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 validate_data.py <data.icsv>")
        sys.exit(1)

    infile = sys.argv[1]
    schemafile = infile.replace(".icsv", "_schema.json")
    outpath = infile.replace(".icsv", "_data_report.txt")
    clean_csv = infile.replace(".icsv", "_clean.csv")

    # --- Step 1: Extract [DATA] section to a clean CSV ---
    try:
        with open(infile, "r", encoding="utf-8") as src, open(clean_csv, "w", newline="", encoding="utf-8") as tgt:
            writer = csv.writer(tgt)
            in_data = False
            for line in src:
                if line.strip() == "# [DATA]":
                    in_data = True
                    continue
                if in_data:
                    if not line.strip().startswith("#") and line.strip():
                        writer.writerow(line.strip().split("|"))  # assumes | delimiter
    except Exception as e:
        print(f"Failed to extract data section: {e}")
        sys.exit(1)

    # --- Step 2: Validate with schema ---
    try:
        resource = Resource(path=clean_csv, schema=schemafile)
        report = resource.validate()

        with open(outpath, "w", encoding="utf-8") as f:
            if report.valid:
                f.write("Data validation OK ✅\n")
            else:
                f.write("Data validation errors:\n")
                for rownum, fieldnum, code, message in report.flatten(["rowNumber", "fieldNumber", "code", "message"]):
                    f.write(f"  Row {rownum or '?'} Col {fieldnum or '?'} [{code}]: {message}\n")

        print(f"Validation report written to {outpath}")

    except Exception as e:
        print(f"Validation failed: {e}")
        sys.exit(1)

    # --- Optional: clean up temporary file ---
    if os.path.exists(clean_csv):
        os.remove(clean_csv)

if __name__ == "__main__":
    main()

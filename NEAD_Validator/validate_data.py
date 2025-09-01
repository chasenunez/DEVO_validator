#!/usr/bin/env python
# validate_data.py: Validate [DATA] rows using the Frictionless schema.

import sys, csv
from frictionless import Resource, Schema
from check_metadata import parse_metadata, check_metadata
from create_schema import build_schema

def main():
    infile = sys.argv[1] if len(sys.argv) > 1 else "data.icsv"
    metadata, fields_meta = parse_metadata(infile)
    schema = build_schema(metadata, fields_meta)
    # Prepare a clean CSV for validation: header + data rows
    clean_csv = "data_clean.csv"
    with open(infile) as src, open(clean_csv, "w", newline='') as tgt:
        reader = csv.reader(src, delimiter=metadata.get("field_delimiter", ","))
        writer = csv.writer(tgt)
        in_data = False
        for row in reader:
            if not row:
                continue
            if row[0].startswith("#"):
                if row[0].strip() == "# [DATA]":
                    in_data = True
                continue
            if in_data:
                if row and row[0]:
                    writer.writerow(row)
    # Now validate using Frictionless
    res = Resource(path=clean_csv, schema=schema)
    report = res.validate()
    out_report = "data_report.txt"
    with open(out_report, "w") as reportf:
        if report.valid:
            reportf.write("OK: Data validation passed.\n")
        else:
            reportf.write("Data validation errors:\n")
            # Flatten errors to list of [row, field, code, message]
            for error in report.flatten(["rowNumber", "fieldNumber", "code", "message"]):
                rownum, colnum, code, msg = error
                reportf.write(f"  Row {rownum or '?'} Field {colnum or '?'}: {msg}\n")
            reportf.write("\nSee above errors to correct the data.\n")
    print(f"Data validation complete. See {out_report} for details.")

if __name__ == "__main__":
    main()

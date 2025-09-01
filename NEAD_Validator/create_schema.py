#!/usr/bin/env python
# create_schema.py: Use metadata to generate a Frictionless schema.

import sys
import json
from frictionless import Schema, fields
# Import the same parse function as above
from check_metadata import parse_metadata, check_metadata

def build_schema(metadata, fields_meta):
    names = fields_meta["fields"]
    types = fields_meta.get("database_fields_data_types", [])
    schema_fields = []
    for i, name in enumerate(names):
        dtype = types[i] if i < len(types) else ""
        dtype = dtype.lower()
        if "timestamp" in dtype or "date" in dtype:
            field = fields.DatetimeField(name=name)
        elif dtype in ("real", "float", "double"):
            field = fields.NumberField(name=name)
        elif dtype in ("integer", "int"):
            field = fields.IntegerField(name=name)
        else:
            field = fields.StringField(name=name)
        schema_fields.append(field)
    schema = Schema(fields=schema_fields)
    # Add missing (nodata) value if provided
    nodata = metadata.get("nodata")
    if nodata:
        schema.missing_values = [str(nodata)]
    return schema

def main():
    infile = sys.argv[1] if len(sys.argv) > 1 else "data.icsv"
    metadata, fields_meta = parse_metadata(infile)
    # Reuse metadata checks to ensure fields list exists
    errors = check_metadata(metadata, fields_meta)
    out_report = "schema_report.txt"
    if errors:
        with open(out_report, "w") as report:
            for err in errors:
                report.write(f"ERROR: {err}\n")
            report.write("\nCannot build schema until metadata issues are resolved.\n")
        print(f"Schema generation aborted. See {out_report} for errors.")
        return
    schema = build_schema(metadata, fields_meta)
    # Save schema JSON
    with open("data_schema.json", "w") as f:
        json.dump(schema.to_descriptor(), f, indent=2)
    with open(out_report, "w") as report:
        report.write("OK: Schema created successfully.\n")
    print(f"Schema written to data_schema.json. Report: {out_report}")

if __name__ == "__main__":
    main()

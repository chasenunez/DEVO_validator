#!/usr/bin/env python3
import re
import json
import sys
from datetime import datetime

def infer_type(values):
    """
    Infer Frictionless field type from a list of sample values.
    """
    for v in values:
        if v in ("-999", "-999.000000", ""):
            continue
        # datetime check
        try:
            datetime.fromisoformat(v)
            return "datetime"
        except Exception:
            pass
        # integer check
        if re.fullmatch(r"-?\d+", v):
            return "integer"
        # number (float) check
        if re.fullmatch(r"-?\d+(\.\d+)?", v):
            return "number"
    return "string"

def parse_icsv_metadata(filepath):
    """
    Extract metadata: field names, standard names, delimiter, and sample data.
    """
    fields, stdnames, delimiter = [], [], "|"
    data_rows = []

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("# fields ="):
                fields = line.split("=", 1)[1].strip().split("|")
            elif line.startswith("# standard_name ="):
                stdnames = line.split("=", 1)[1].strip().split("|")
            elif line.startswith("# field_delimiter"):
                delimiter = line.split("=", 1)[1].strip()
            elif not line.startswith("#") and line:
                data_rows.append(line.split(delimiter))

    return fields, stdnames, delimiter, data_rows

def build_schema(fields, stdnames, data_rows):
    """
    Build a Table Schema dictionary with richer typing and constraints.
    """
    schema = {"fields": [], "missingValues": ["-999", "-999.000000"]}

    # transpose data to sample per column
    columns = list(zip(*data_rows)) if data_rows else [[] for _ in fields]

    for i, name in enumerate(fields):
        desc = stdnames[i] if i < len(stdnames) else ""
        sample_values = columns[i][:50] if columns else []
        ftype = infer_type(sample_values)

        field_schema = {"name": name, "type": ftype}
        if desc:
            field_schema["description"] = desc

        # add constraints for known fields
        if name.lower() == "timestamp":
            field_schema["constraints"] = {"required": True}
            field_schema["format"] = "any"
        elif name.upper() == "RH":  # relative humidity
            field_schema["constraints"] = {"minimum": 0, "maximum": 1}
        elif name.upper() == "TA":  # air temperature
            field_schema["constraints"] = {"minimum": -100, "maximum": 60}

        schema["fields"].append(field_schema)

    return schema

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 create_schema.py <data.icsv>")
        sys.exit(1)

    filepath = sys.argv[1]
    fields, stdnames, delimiter, data_rows = parse_icsv_metadata(filepath)
    schema = build_schema(fields, stdnames, data_rows)

    outpath = filepath.replace(".icsv", "_schema.json")
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)

    print(f"Schema written to {outpath}")

if __name__ == "__main__":
    main()

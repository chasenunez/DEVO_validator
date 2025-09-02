#!/usr/bin/env python3
import sys
from frictionless import Resource, validate

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 validate_data.py <data.icsv>")
        sys.exit(1)

    filepath = sys.argv[1]
    schemafile = filepath.replace(".icsv", "_schema.json")

    try:
        resource = Resource(
            path=filepath,
            schema=schemafile,
            format="csv",
            dialect={
                "delimiter": "|",
                "header": False   # iCSV has no header row in the [DATA] section
            }
        )

        report = validate(resource)

        outpath = filepath.replace(".icsv", "_data_report.txt")
        with open(outpath, "w", encoding="utf-8") as f:
            if report.valid:
                f.write("Data validation OK ✅\n")
            else:
                f.write("Data validation errors:\n")
                for task in report.tasks:
                    for error in task["errors"]:
                        f.write(f"  - {error['message']}\n")

        print(f"Validation report written to {outpath}")

    except Exception as e:
        print(f"Validation failed: {e}")

if __name__ == "__main__":
    main()

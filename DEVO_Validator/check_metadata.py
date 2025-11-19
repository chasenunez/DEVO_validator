#!/usr/bin/env python
# check_metadata.py: Parse the NEAD/iCSV file and verify metadata consistency.

import sys

def parse_metadata(filename):
    metadata = {}
    fields_meta = {}
    section = None
    with open(filename) as f:
        for line in f:
            line = line.rstrip("\n")
            # Detect section headers
            if line.strip() == "# [METADATA]":
                section = "metadata"
                continue
            if line.strip() == "# [FIELDS]":
                section = "fields"
                continue
            if line.strip() == "# [DATA]":
                section = None
                break  # metadata/fields done

            if line.startswith("#") and section:
                content = line.lstrip("#").strip()
                if "=" in content:
                    key, value = content.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if section == "metadata":
                        metadata[key] = value
                    elif section == "fields":
                        # Split values by the field_delimiter (to be set from metadata)
                        delim = metadata.get("field_delimiter", ",")
                        values = [v.strip() for v in value.split(delim)]
                        fields_meta[key] = values
    return metadata, fields_meta

def check_metadata(metadata, fields_meta):
    errors = []
    # Check required metadata keys
    for req in ["field_delimiter", "geometry", "srid"]:
        if req not in metadata or not metadata[req]:
            errors.append(f"Missing required metadata: {req}")
    if "fields" not in fields_meta:
        errors.append("Missing required FIELDS list 'fields'")
    else:
        num = len(fields_meta["fields"])
        # Ensure all fields-section lists match the number of fields
        for key, values in fields_meta.items():
            if key != "fields" and values and len(values) != num:
                errors.append(f"Inconsistent count in '{key}': expected {num}, found {len(values)}")
    return errors

def main():
    infile = sys.argv[1] if len(sys.argv) > 1 else "data.icsv"
    metadata, fields_meta = parse_metadata(infile)
    errors = check_metadata(metadata, fields_meta)
    out_report = "metadata_report.txt"
    with open(out_report, "w") as report:
        if errors:
            for err in errors:
                report.write(f"ERROR: {err}\n")
            report.write("\nPlease fix metadata issues above.\n")
        else:
            report.write("OK: Metadata checks passed.\n")
    print(f"Metadata check complete. See {out_report} for details.")

if __name__ == "__main__":
    main()

"this code has been deprecated and moved into the NEAD_Validator"
import re
import csv
import json
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional
import pandas as pd
from frictionless import Schema, Resource, validate
from io import StringIO 

# ---------- Configuration: expected metadata keys & fallback schema ----------
REQUIRED_METADATA_KEYS = [
    "field_delimiter",  # example key often present in icsv
    # Add any other keys you want to require
]

FALLBACK_METADATA_SCHEMA_DESCRIPTOR = {
    "fields": [
        {"name": "Site.ID", "type": "integer", "constraints": {"required": True}},
        {"name": "Biomasstype", "type": "string", "constraints": {"required": True, "enum": ["Living", "Litter"]}},
        {"name": "Site", "type": "string", "constraints": {"required": True}},
        {"name": "Invasion", "type": "string", "constraints": {"required": True, "enum": ["Native", "Invaded"]}},
        {"name": "Treatment", "type": "string", "constraints": {"required": True, "enum": ["Open", "No livestock", "No mammals", "No insects"]}},
        {"name": "Weight_20by100_cm", "type": "number", "constraints": {"required": True, "minimum": 0}},
        {"name": "sample_type", "type": "string", "constraints": {"required": False}},
    ],
    "missingValues": ["", "NA"]
}

# ---------- Helpers: parse file into metadata dict + pandas DataFrame ----------
def split_metadata_and_csv(file_path: Path, sniff_lines: int = 500) -> Tuple[Dict[str, str], str]:
    """
    Split an iCSV file into metadata dict and CSV text.
    Behavior:
      - If the file contains a "METADATA:" marker (case-insensitive), collect everything
        from after that marker up to the "Data:" marker as metadata.
      - Parse key:value lines from that block into metadata dict.
      - Find the first likely CSV header line after "Data:" and return the CSV text from there.
      - If markers are not present, fall back to heuristics (previous implementation).
    """
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    n = len(lines)

    # Search for METADATA: and Data: markers (case-insensitive)
    meta_idx = None
    data_idx = None
    for i, line in enumerate(lines[:sniff_lines]):
        if re.match(r'^\s*METADATA\s*:?\s*$', line, flags=re.IGNORECASE):
            meta_idx = i
            # find data marker after metadata
            for j in range(i + 1, min(n, sniff_lines)):
                if re.match(r'^\s*Data\s*:?\s*$', lines[j], flags=re.IGNORECASE):
                    data_idx = j
                    break
            break
        # also handle the case "METADATA: key: value" where metadata content starts on same line
        m_inline = re.match(r'^\s*METADATA\s*:\s*(.*)$', line, flags=re.IGNORECASE)
        if m_inline:
            meta_idx = i
            # create a pseudo next line with the inline content
            # but prefer to keep parsing below; find Data: anyway
            for j in range(i + 1, min(n, sniff_lines)):
                if re.match(r'^\s*Data\s*:?\s*$', lines[j], flags=re.IGNORECASE):
                    data_idx = j
                    break
            break

    # If we found both markers, use them deterministically
    metadata_lines = []
    csv_start_index = 0
    if meta_idx is not None:
        # Determine metadata block: lines between meta_idx and data_idx (if present)
        start = meta_idx + 1
        end = data_idx if data_idx is not None else min(n, sniff_lines)
        # collect block
        metadata_lines = lines[start:end]
        # If there was inline content on the METADATA: line, try extracting it
        inline_meta = re.match(r'^\s*METADATA\s*:\s*(.*)$', lines[meta_idx], flags=re.IGNORECASE)
        if inline_meta and inline_meta.group(1).strip():
            metadata_lines.insert(0, inline_meta.group(1).strip())

        # Determine where the CSV starts: after the Data: marker if present
        if data_idx is not None:
            # find the first non-empty line after data_idx that looks like a header (contains a delimiter)
            for k in range(data_idx + 1, n):
                l = lines[k].strip()
                if not l:
                    continue
                # treat as header if it contains comma, semicolon, tab, or many words separated by spaces (fallback)
                if any(d in l for d in [",", ";", "\t", "|", ":"]):
                    csv_start_index = k
                    break
                # If line looks like CSV header without delimiters (rare), accept if next line has numeric tokens
                next_line = lines[k + 1].strip() if k + 1 < n else ""
                # quick heuristic: header with words and next has digits or 'NA' tokens
                if re.search(r'[A-Za-z]', l) and re.search(r'(\d|NA)', next_line):
                    csv_start_index = k
                    break
            else:
                # no clear header found, set csv_start_index to data_idx + 1 (will be handled later)
                csv_start_index = data_idx + 1
        else:
            # no explicit Data: marker; fallback to first line after metadata block
            csv_start_index = end
    else:
        # fallback: previous heuristics (scan for leading key:value pairs or detect header)
        # collect leading "key: value" style lines as metadata candidates
        for i, line in enumerate(lines[:sniff_lines]):
            if re.search(r':', line) and line.count(',') <= 1:
                metadata_lines.append(line)
                continue
            if ',' in line or ';' in line or '\t' in line:
                delim = ',' if ',' in line else (';' if ';' in line else '\t')
                header_count = line.count(delim)
                similar = 0
                for nxt in lines[i+1:i+6]:
                    if nxt.count(delim) >= header_count:
                        similar += 1
                if similar >= 1:
                    csv_start_index = i
                    break
        else:
            csv_start_index = 0

    # Build metadata dict from metadata_lines: parse key: value entries
    metadata = {}
    for ml in metadata_lines:
        ml_strip = ml.strip()
        if not ml_strip:
            continue
        # some metadata blocks include headings like "Required:" or "Recommended:"; skip single-word headings
        if re.match(r'^[A-Za-z- ]+:\s*$', ml_strip) and ':' not in ml_strip.rstrip(':'):
            # if it's only a heading like "Required:" keep it as a heading entry with empty value
            # but more commonly these are just separators; we skip them to avoid noise
            # skip if the line ends with ":" and nothing after
            if re.match(r'^[A-Za-z -]+:\s*$', ml_strip):
                continue
        m = re.match(r'^\s*([^:]+)\s*:\s*(.*)$', ml_strip)
        if m:
            key = m.group(1).strip()
            value = m.group(2).strip()
            metadata[key] = value
        else:
            # fallback: store whole line with auto key
            metadata_key = f"_meta_line_{len(metadata)+1}"
            metadata[metadata_key] = ml_strip

    csv_text = "\n".join(lines[csv_start_index:]).lstrip("\n")
    return metadata, csv_text

    # ---------- Metadata validation ----------
def check_metadata_completeness(metadata: Dict[str, str], required_keys: List[str]) -> Dict[str, Any]:
    problems = []
    for k in required_keys:
        if k not in metadata:
            problems.append(f"Missing required metadata key: '{k}'")
        else:
            if metadata[k] is None or str(metadata[k]).strip() == "":
                problems.append(f"Metadata key '{k}' is present but empty")

    if "field_delimiter" in metadata:
        if metadata["field_delimiter"] not in [",", ";", "\t", "|", ":", " "]:
            problems.append(
                f"Unusual field_delimiter '{metadata['field_delimiter']}'. If your CSV uses commas, set field_delimiter to ','"
            )
    return {"ok": len(problems) == 0, "problems": problems}

    # ---------- Build frictionless schema from metadata OR fallback descriptor ----------
def build_frictionless_schema_from_metadata(metadata: Dict[str, str],
                                            fallback_descriptor: Optional[Dict] = None,
                                            df: Optional[pd.DataFrame] = None) -> Schema:
    if "fields" in metadata:
        val = metadata["fields"]
        fields = None
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                fields = parsed
        except Exception:
            fields = [c.strip() for c in re.split(r'[,;|:]+', val) if c.strip()]
        if fields and df is not None:
            descriptor_fields = []
            for col in fields:
                if col not in df.columns:
                    descriptor_fields.append({"name": col, "type": "string", "constraints": {"required": False}})
                else:
                    dtype = df[col].dtype
                    if pd.api.types.is_integer_dtype(dtype):
                        ftype = "integer"
                    elif pd.api.types.is_float_dtype(dtype):
                        ftype = "number"
                    else:
                        ftype = "string"
                    descriptor_fields.append({"name": col, "type": ftype})
            descriptor = {"fields": descriptor_fields}
            return Schema(descriptor)

    if "schema" in metadata:
        try:
            descriptor = json.loads(metadata["schema"])
            return Schema(descriptor)
        except Exception:
            pass

    if fallback_descriptor is not None:
        return Schema(fallback_descriptor)

    if df is not None:
        descriptor_fields = []
        for col in df.columns:
            dtype = df[col].dtype
            if pd.api.types.is_integer_dtype(dtype):
                ftype = "integer"
            elif pd.api.types.is_float_dtype(dtype):
                ftype = "number"
            else:
                unique_vals = df[col].dropna().unique()
                if 0 < len(unique_vals) <= 10 and all(isinstance(v, str) for v in unique_vals):
                    ftype = "string"
                    descriptor_fields.append({"name": col, "type": ftype, "constraints": {"required": False, "enum": list(map(str, unique_vals))}})
                    continue
                ftype = "string"
            descriptor_fields.append({"name": col, "type": ftype, "constraints": {"required": False}})
        descriptor = {"fields": descriptor_fields, "missingValues": ["", "NA"]}
        return Schema(descriptor)

    raise ValueError("Cannot build schema: no metadata, no fallback, no dataframe")

    # ---------- Validate data with frictionless and collect readable errors ----------
def validate_data_with_schema(df: pd.DataFrame, schema: Schema, csv_path: Optional[Path] = None) -> Dict[str, Any]:
    if csv_path is not None:
        resource = Resource(path=str(csv_path), schema=schema)
    else:
        resource = Resource(data=df, schema=schema)

    report = validate(resource)
    errors = []
    try:
        flattened = report.flatten() if hasattr(report, "flatten") else None
        if flattened:
            for e in flattened:
                errors.append(e)
    except Exception:
        pass

    if not errors:
        if hasattr(report, "errors") and report.errors:
            errors = report.errors
        else:
            try:
                tasks = report.to_descriptor().get("tasks", [])
                for t in tasks:
                    for e in t.get("errors", []):
                        errors.append(e)
            except Exception:
                errors = [str(report)]

    return {"valid": report.valid, "errors": errors, "report": report}

    # ---------- Human-readable error report generator ----------
def human_readable_report(metadata_checks: Dict[str, Any],
                          metadata: Dict[str, str],
                          data_validation: Dict[str, Any]) -> str:
    lines = []
    lines.append("==== METADATA CHECK ====")
    if metadata_checks["ok"]:
        lines.append("Metadata status: OK (required keys are present).")
    else:
        lines.append("Metadata status: PROBLEMS FOUND")
        for p in metadata_checks["problems"]:
            lines.append(f"  - {p}")

    lines.append("")
    lines.append("Metadata content:")
    if metadata:
        for k, v in metadata.items():
            lines.append(f"  {k}: {v}")
    else:
        lines.append("  (No metadata detected)")

    lines.append("\n==== SCHEMA USED (frictionless descriptor) ====")
    try:
        schema_desc = data_validation["report"].to_descriptor().get("tasks", [{}])[0].get("resource", {}).get("schema")
        if not schema_desc and "report" in data_validation:
            schema_obj = data_validation["report"]
            schema_desc = getattr(schema_obj, "schema", None)
    except Exception:
        schema_desc = None

    if schema_desc:
        lines.append(json.dumps(schema_desc, indent=2))
    else:
        lines.append(" (failed to retrieve descriptor; schema object available in program output)")

    lines.append("\n==== DATA VALIDATION ====")
    if data_validation["valid"]:
        lines.append("Data validation: PASSED")
    else:
        lines.append("Data validation: FAILED")
        lines.append("Errors found:")
        errs = data_validation["errors"]
        if not errs:
            lines.append("  (No structured errors available; see full frictionless report below.)")
            lines.append(str(data_validation.get("report")))
        else:
            for e in errs:
                if isinstance(e, dict):
                    code = e.get("code") or e.get("error") or e.get("type")
                    msg = e.get("message") or e.get("note") or str(e)
                    row = e.get("rowNumber") or e.get("row") or e.get("row-number")
                    field = e.get("fieldNumber") or e.get("fieldName") or e.get("name")
                    loc = []
                    if row is not None:
                        loc.append(f"row {row}")
                    if field:
                        loc.append(f"field '{field}'")
                    loc_text = ", ".join(loc) if loc else "unknown location"
                    lines.append(f"  - [{code}] {msg}  ({loc_text})")
                else:
                    lines.append(f"  - {str(e)}")

    lines.append("\n==== SUGGESTED FIXES ====")
    if not metadata_checks["ok"]:
        lines.append("Metadata suggestions:")
        for p in metadata_checks["problems"]:
            lines.append(f"  - {p}")
        lines.append("  - Ensure metadata keys follow the icsv structural guidelines (e.g. 'field_delimiter', 'geometry', 'srid', 'fields', ...).")
    else:
        lines.append("Metadata looks OK (see above).")

    if not data_validation["valid"]:
        lines.append("Data suggestions:")
        for e in data_validation["errors"]:
            if isinstance(e, dict):
                msg = e.get("message") or e.get("note") or str(e)
                field = e.get("fieldName") or e.get("field") or e.get("fieldNumber")
                row = e.get("rowNumber") or e.get("row")
                if field or row:
                    lines.append(f"  - Fix {('field '+str(field)) if field else ''} {('in row '+str(row)) if row else ''}: {msg}")
                else:
                    lines.append(f"  - {msg}")
            else:
                lines.append(f"  - {str(e)}")
        lines.append("  - Common fixes: remove or correct non-numeric tokens in numeric columns (e.g. 'error', 'red'), replace empty required cells with valid values or 'NA' if allowed, remove entirely empty rows.")
    else:
        lines.append("Data looks valid with respect to the schema.")

    lines.append("\n==== END OF REPORT ====")
    return "\n".join(lines)

    # ---------- Main routine tying everything together ----------
def validate_icsv_file(path: str,
                       required_metadata_keys: List[str] = REQUIRED_METADATA_KEYS,
                       fallback_schema_descriptor: Optional[Dict] = FALLBACK_METADATA_SCHEMA_DESCRIPTOR) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)

    metadata, csv_text = split_metadata_and_csv(p)

    # Prefer delimiter from metadata if present
    delimiter = metadata.get("field_delimiter", None)
    if delimiter:
        if delimiter.lower() in [":", "colon"]:
            delim = ":"
        elif delimiter.lower() in [",", "comma"]:
            delim = ","
        elif delimiter.lower() in [";", "semicolon"]:
            delim = ";"
        elif delimiter.lower() in ["\t", "tab"]:
            delim = "\t"
        else:
            delim = delimiter
    else:
        delim = None

    # Read into DataFrame (try using the file path first so Frictionless can pick up native parsing)
    try:
        if delim:
            df = pd.read_csv(p, delimiter=delim, na_values=["NA", ""])
        else:
            df = pd.read_csv(p, na_values=["NA", ""])
    except Exception:
        # fallback: read csv_text (the portion we sliced) - allow pandas to infer
        try:
            df = pd.read_csv(pd.compat.StringIO(csv_text), na_values=["NA", ""])
        except Exception:
            # ultimate fallback: parse with csv.reader
            rows = list(csv.reader(csv_text.splitlines()))
            df = pd.DataFrame(rows[1:], columns=rows[0] if rows else None)

    metadata_checks = check_metadata_completeness(metadata, required_metadata_keys)
    schema = build_frictionless_schema_from_metadata(metadata, fallback_descriptor=fallback_schema_descriptor, df=df)
    data_validation = validate_data_with_schema(df=df, schema=schema, csv_path=p)
    report_text = human_readable_report(metadata_checks, metadata, data_validation)

    return {
        "metadata": metadata,
        "metadata_checks": metadata_checks,
        "schema": schema,
        "dataframe": df,
        "data_validation": data_validation,
        "report_text": report_text
    }
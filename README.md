# DEVO_validator

Validates self-documenting CSV files (iCSV / NEAD format — files where the first lines are a `#`-prefixed header containing `[METADATA]`, `[FIELDS]`, `[DATA]` sections). The tool parses the header, builds a [Frictionless](https://framework.frictionlessdata.io/) schema from the metadata, and validates the data section against it.

Sister tool to **DEVO_enricher**, which produces the iCSV files in the first place. The pipeline:

```
       User                           Admin
     Front-End                       Back-End 
┌─────────────────┐ ┌──────────────────────────────────────────┐
│                 │ │                        ┌─────────────┐   │
│ ┌─────────────┐ │ │  ┌────────────────┐    │  Validation │   │
│ │   Standard  │ │ │  │                ├───►│    Schema   ├─┐ │
│ │  .CSV file  ├─┼─┼─►│      DEVO      │    └─────────────┘ │ │
│ └─────────────┘ │ │  │    enricher    │    ┌─────────────┐ │ │
│                 │ │  │                ├───►│   Enriched  │ │ │
│                 │ │  └────────────────┘    │  .iCSV file ├─┤ │
│                 │ │                        └─────────────┘ │ │
│               ◄─┼─┼────────────────────────────────────────┘ │
│                 │ │                        ┌─────────────┐   │
│                 │ │  ┌────────────────┐    │ Informative │   │
│ ┌─────────────┐ │ │  │                ├───►│    Errors   ├─┐ │
│ │   Enriched  │ │ │  │    **DEVO**    │    └─────────────┘ │ │
│ │  .iCSV file ├─┼─┼─►│  **validator** │    ┌─────────────┐ │ │
│ └─────────────┘ │ │  │                ├───►│  Validated  │ │ │
│                 │ │  └────────────────┘    │ .iCSV file  ├─┤ │
│                 │ │                        └─────────────┘ │ │
│               ◄─┼─┼────────────────────────────────────────┘ │
│ ┌─────────────┐ │ │  ┌────────────────┬──── To EnviDat Repo ─┼──►
│ │  Validated  │─┼─┼─►│   WSL/ENVIDAT  │    ┌─────────────┐   │
│ │ .iCSV file  │ │ │  │    UPLOADER    ├───►│     DOI     ├─┐ │
│ └─────────────┘ │ │  └────────────────┘    └─────────────┘ │ │
│               ◄─┼─┼────────────────────────────────────────┘ │
└─────────────────┘ └──────────────────────────────────────────┘
```

## Run

```bash
python3 DEVO_validate.py data.icsv          # one file
python3 DEVO_validate.py *.icsv             # batch
```

For each input `data.icsv` you get:

| File | What |
|---|---|
| `data_metadata_report.txt` | `[PASS]` or a list of metadata problems |
| `data_schema.json` | Frictionless schema built from the metadata |
| `data_schema_report.txt` | `[PASS]` or schema-construction errors |
| `data_data_report.txt` | `[PASS]` or row/column/type errors |

Pass means the report contains `Data validation OK [PASS]`.

## Files

| Script | Step |
|---|---|
| `DEVO_validate.py` | Wrapper — runs the three steps below in order |
| `check_metadata.py` | Parse `[METADATA]` + `[FIELDS]`, check required keys |
| `create_schema.py` | Build the Frictionless schema from the metadata |
| `validate_data.py` | Extract the `[DATA]` block to a clean CSV, run validation |
| `data.icsv` | Sample input |

## Input format

Either iCSV or NEAD. Minimal example:

```
# iCSV 1.0 UTF-8
# [METADATA]
# field_delimiter = |
# srid = EPSG:21781
# nodata = -999
# [FIELDS]
# fields = timestamp|TA|RH
# database_fields_data_types = timestamp,real,real
# [DATA]
2005-08-23T15:30:00|-999|50
2005-08-23T16:30:00|1.5|45.2
```

Required metadata keys: `field_delimiter`, `srid`, `geometry`. The `fields` list length must match other field-arrays (`database_fields_data_types`, `units`, `scale_factor`).

## Why Frictionless

Frictionless is small, well-maintained, and used in repositories like [Dryad](https://blog.datadryad.org/2020/11/18/frictionless-data/) and [GBIF](https://data-blog.gbif.org/post/frictionless-data-and-darwin-core/) for the same job. We built on top instead of inventing a schema language.

## Customising

- Edit `check_metadata.py` to add or relax metadata rules.
- Edit `create_schema.py` to change type-mapping or add constraints (`enum`, `minimum`, `maximum`).
- Edit `validate_data.py` to add custom Frictionless checks.

To add an enum constraint, edit the generated schema JSON:

```json
{
  "fields": [
    {"name": "Invasion", "type": "string", "constraints": {"enum": ["Native", "Invaded"]}}
  ]
}
```

## See also

- [Frictionless Framework](https://framework.frictionlessdata.io/)
- [Frictionless checks](https://framework.frictionlessdata.io/docs/checks/)
- [Open Data Editor](https://okfn.org/en/projects/open-data-editor/)

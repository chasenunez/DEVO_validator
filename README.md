# NEAD Validator — lightweight QA/QC for self-documented CSVs (NEAD / iCSV)

**NEAD Validator** is a small, modular Python tool that:
- ingests *self-documented* CSV files (NEAD / iCSV) containing `[METADATA]`, `[FIELDS]`, and `[DATA]` sections,
- validates required metadata,
- builds a Frictionless-compatible schema from that metadata, and
- validates the data using the Frictionless framework.

This README explains what the tool does, how to run it, and shows clear examples.



## 1. Quick introduction & links

This project uses the **Frictionless Framework** to express table schemas and run automated checks. Frictionless is a small, well-maintained toolkit for tabular data validation and packaging: https://framework.frictionlessdata.io/. It could be beneficial for use cases like **[EnviDat](https://www.envidat.ch/#/)**, where the integrity and reliability of metadata and data are critical for [long term storage and reuse](https://www.dora.lib4ri.ch/wsl/islandora/object/wsl:18703). It has been used successfully in similar repositories like [DRYAD](https://blog.datadryad.org/2020/11/18/frictionless-data/) and the [Global Biodiversity Information Facility (GBIF)](https://data-blog.gbif.org/post/frictionless-data-and-darwin-core/) for data validation and quality control.

### 2. **Big Picture: Why Frictionless for EnviDat?**

For **EnviDat**, quality assurance (QA) and control (QC) of uploaded ecological datasets and their metadata is essential. Frictionless offers:

* **Flexibility**: Researchers can validate their own datasets using a graphical interface (**[Open Data Editor](https://okfn.org/en/projects/open-data-editor/)**) while SciIT staff can run backend metadata and data checks through Python scripts like `NEAD_validator` in this repo.

* **Catches Common as well as Specific Errors**: Missing values, incorrect types, or malformed columns are offered out of the box, but common data error in ecological data can be added via a custom schema. 

* **Works with *self-documented**: `NEAD Validator` is designed to work with self-documented CSV formats like NEAD/iCSV where metadata are imbeded in the file header. `NEAD_Validator` further checks for correspondence between the metadata and the data, and then uses that information to check the data.



## 2. Content

```

nead_validator/
├─ nead_validate.py         # wrapper: runs three steps on one or more files
├─ check_metadata.py        # parse + metadata checks (produces <file> metadata_report.txt)
├─ create_schema.py         # build schema from metadata (writes <file> schema.json and <file>_schema_report.txt)
├─ validate_data.py         # validate data using schema (writes <file> data_report.txt)
└─ data.icsv                 # dataset to be run

```

## 4. How to run (single command)

The wrapper `nead_validate.py` is provided to run the full pipeline for one or more files:

```bash
# single file
python3 nead_validate.py data.icsv

# multiple files (shell glob)
python3 nead_validate.py *.icsv file2.icsv
```

Each input file will produce a set of dataset-specific outputs:

```
data_metadata_report.txt       # metadata validation results
data_schema.json               # frictionless schema built from metadata
data_schema_report.txt         # schema creation status
data_clean.csv                 # (temporary) extracted [DATA] for validation
data_data_report.txt           # data validation results (contains human-readable messages)
```

If `data_data_report.txt` contains:

```
Data validation OK [PASS]
```

the file passed validation. If not, the report lists row/column/type messages to fix.



## 5. File format examples

### Minimal NEAD example

```
# NEAD 1.0 UTF-8
# [METADATA]
# field_delimiter = ,
# srid = EPSG:4326
# geometry = POINTZ (38.5053 72.5794 3199)
# nodata = -999
# [FIELDS]
# fields = timestamp,TA1,TA2
# database_fields_data_types = timestamp,real,real
# [DATA]
1996-05-12 11:00:00+00, -999, 1.23
1996-05-12 12:00:00+00, 2.34, -999
```

### Minimal iCSV example (pipe `|` delimiter)

```
# iCSV 1.0 UTF-8
# [METADATA]
# field_delimiter = |
# srid = EPSG:21781
# nodata = -999.000000
# [FIELDS]
# fields = timestamp|TA|RH
# database_fields_data_types = timestamp,real,real
# [DATA]
2005-08-23T15:30:00|-999|50
2005-08-23T16:30:00|1.5|45.2
```



## 6. Example run & sample output

1. Run:

```bash
python3 nead_validate.py sample.icsv
```

2. Files produced:

* `sample_metadata_report.txt`

  ```
  OK: Metadata checks passed [PASS]
  ```
* `sample_schema.json`

  ```json
  {
    "fields": [
      {"name": "timestamp", "type": "datetime"},
      {"name": "TA", "type": "number"},
      {"name": "RH", "type": "number"}
    ],
    "missingValues": ["-999"]
  }
  ```
* `sample_schema_report.txt`

  ```
  OK: Schema created successfully [PASS]
  ```
* `sample_data_report.txt` (if there are issues)

  ```
  Data validation errors [FAIL]:
    Row 5 Col 2 [type-error]: "abc" is not a number
    Row 8 Col 1 [datetime-error]: "1996-xx-12" is not a valid datetime
  ```

  or (if clean)

  ```
  Data validation OK [PASS]
  ```



## 7. What the pipeline does (step-by-step)

1. **Metadata parsing & checks** (`check_metadata.py`)

   * Reads header lines starting with `#` and identifies `[METADATA]` and `[FIELDS]`.
   * Validates required metadata keys exist: e.g. `field_delimiter`, `srid`, `geometry`.
   * Checks the `fields` list length matches other FIELDS entries (e.g. `database_fields_data_types`, `units`, `scale_factor`).
   * Writes `<file>_metadata_report.txt` summarizing problems or `[PASS]`.

2. **Schema creation** (`create_schema.py`)

   * Maps `database_fields_data_types` (or reasonable defaults/inference) to Frictionless field types (`datetime`, `number`, `integer`, `string`).
   * Includes the `nodata` sentinel in `missingValues`.
   * Writes `<file>_schema.json` and `<file>_schema_report.txt`.

3. **Data extraction & validation** (`validate_data.py`)

   * Extracts the `[DATA]` block into a clean CSV (no metadata/comments).
   * Loads the `<file>_schema.json` as a Frictionless schema and validates the clean CSV.
   * Writes `<file>_data_report.txt` with row/column/type errors or `[PASS]`.



## 8. Developing / customizing

* The repository is intentionally modular:

  * Edit `check_metadata.py` to add or relax metadata rules.
  * Edit `create_schema.py` to change type-mapping rules or add constraints (e.g., ranges, `enum` lists).
  * Edit `validate_data.py` to include extra Frictionless checks (baseline checks, custom checks).
* To add custom constraints (e.g., `enum`, `minimum`, `maximum`), extend fields in the generated schema JSON. Frictionless will enforce those at validation time.

**Example: adding an enum(eration) constraint in schema**

```json
{
  "fields": [
    {"name": "Invasion", "type": "string", "constraints": {"enum": ["Native", "Invaded"]}}
  ]
}
```


## 11. Resources & links

* [Frictionless framework](https://framework.frictionlessdata.io/)
* [Frictionless checks docs](https://framework.frictionlessdata.io/docs/checks/)
* [Frictionless schema docs](https://framework.frictionlessdata.io/docs/framework/schema.html)
* [Open Data Editor](https://okfn.org/en/projects/open-data-editor/)
* [Example Frictionless notebook (tutorial)](https://colab.research.google.com/github/frictionlessdata/frictionless-py)
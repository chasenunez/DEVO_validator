### 1. **Introduction to the Frictionless Framework**

The **[Frictionless Framework](https://framework.frictionlessdata.io/)** offers [open-source tools](https://github.com/frictionlessdata) that help manage and ensure data quality. It’s ideal for use cases like **[EnviDat](https://www.envidat.ch/#/)**, where the integrity and reliability of data are critical for [long term storage and reuse](https://www.dora.lib4ri.ch/wsl/islandora/object/wsl:18703). It has been used successfully in similar repositories like [DRYAD](https://blog.datadryad.org/2020/11/18/frictionless-data/) and the [Global Biodiversity Information Facility (GBIF)](https://data-blog.gbif.org/post/frictionless-data-and-darwin-core/) for data validation and quality control.

### 2. **Big Picture: Why Frictionless for EnviDat?**

For **EnviDat**, quality assurance (QA) and control (QC) of uploaded ecological datasets is essential. Frictionless:

* **Flexibility**: Researchers can validate their own datasets using a graphical interface (Open Data Editor) while IT staff can run backend checks through Python scripts.
* **Automates the Validation Process**: Ensures all incoming data fits the expected structure, types, and constraints prior to ingestion.
* **Catches Common as well as Specific Errors**: Missing values, incorrect types, or malformed columns are standard, but common data error in ecological data can be added via a custom schema. 

### 3. **How Frictionless Can Be Incorporated into WSL's Workflow**

* **Researchers' Workflow**:
  * Use **[Open Data Editor](https://okfn.org/en/projects/open-data-editor/)** (GUI) to perform quality assurance (QA) checks before uploading datasets.
  * Researchers can view and fix errors interactively.

* **IT Staff's Workflow**:

  * IT staff can automate quality control (QC) checks using **Frictionless in Python scripts**.
  * This can be integrated into the data upload process for backend validation.

### 4. **Example Dataset with Errors**

Let’s take a look at a **subsample of a real ecological dataset** uploaded to EnviDat (Biomass), but we will introduce some intentional errors (missing values, blank headers, blank rows, NA's, data type error, etc.).

Original data have no errors, and come from _"Herbivory mediates the response of below-ground food-webs to invasive grasses"_, published in the _Journal of Animal Ecology_.
> _Fioratti, M., Cordero, I., Chinn, N., Firn, J., Holmes, J., Klein, M., Lebbink, G., Nielsen, U., Schütz, M., Zimmermann, S., Risch, A. C. (2025). Herbivory mediates the response of below-ground food-webs to invasive grasses. EnviDat. https://www.doi.org/10.16904/envidat.677._

```python
import pandas as pd
from pathlib import Path

csv_text = """
Site.ID,Biomasstype,Site,Invasion,Treatment,Weight_20by100_cm,sample_type
1,Litter,PnK,Native,Open,15.515,
1,Living,PnK,Native,Open,95.89,
2,Litter,PnK,Native,No livestock,39.14,
2,Living,PnK,,No livestock,177.355,
3,Litter,PnK,Native,No mammals,38.95,
error,Living,PnK,Native,No mammals,117.16,
,,,,,,
,,,,,,red
9,Litter,Vivan,Native,Open,NA,
9,Living,Vivan,Native,Open,86.74,
10,Litter,Vivan,Native,No livestock,79.08,
10,Living,Vivan,Native,No livestock,110.51,
11,Litter,Vivan,Native,No mammals,85.83,
11,Living,Vivan,Native,No mammals,114.195,
""".strip()+"\n"

Path("biomass_sample.csv").write_text(csv_text, encoding="utf-8")
print("Wrote biomass_sample.csv")
"""

# Load the dataset into pandas DataFrame
df = pd.read_csv(StringIO(data))
df.head()  # Displaying the first few rows of the dataset
```
### 5. **Step-by-Step: How Frictionless Helps QC and QA**

#### 5.1 **Using the Open Data Editor (GUI) for QA**:

Researchers can use the **[Open Data Editor](https://okfn.org/en/projects/open-data-editor/)** to interactively validate their datasets before uploading them to EnviDat. The Open Data Editor provides a graphical interface that checks data quality in real-time.

* **What the Open Data Editor Can Catch**:

  * **Missing values** (e.g., "NA" entries in `Weight_20by100_cm` column).
  * **Incorrect data types** (e.g., text in numeric fields).
  * **Empty or missing columns**.
  * **Outliers** (values that fall outside the expected range).

#### Example: Fixing Missing Data in the Open Data Editor (GUI)

Researchers can open their dataset, visualize errors, and directly modify them in the GUI. If a field has missing values, users can choose to replace them with the average or a specific value.

[ADD GRAPHICS HERE OF THIS EXAMPLE IN GUI FIX MODE]

#### 5.2 **Using Frictionless in Python for Backend Validation (QC)**:

Once the preliminary check has been done by the researchers, Scientific IT staff can run a Python script (or work in the console) to validate datasets automatically before upload. This is done by defining a custom **schema** that specifies the expected structure and rules for the dataset.

```python
# Install Frictionless Framework if necessary
!pip install frictionless
```
### 5.3 **What Errors Does the Default Schema Catch?**

* **Missing or null values** (e.g., NA in numerical fields).
* **Type mismatches** (e.g., text in numeric columns).
* **Invalid values** (e.g., `Invasion` should be either "Native" or "Invaded").
* **Duplicate rows** or columns.
* **Empty or missing headers**.

#### 5.4 **Custom Schema**:

You can **extend the default schema** to suit your own data structure. For example, you can set custom ranges for numeric columns, specific formats for strings, and define additional validation rules (e.g., a specific regex pattern for site names).

```python
ffrom frictionless import Schema

schema = Schema({
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
})
```
```python
from frictionless import Resource, validate

resource = Resource(path="biomass_sample.csv", schema=schema)
report = validate(resource)
print(report.valid)
```
Multi-table validation:
```python
from frictionless import Package, Resource, validate
package = Package(resources=[
Resource(name="ecological_data", path="biomass_sample.csv", schema=schema),
])

report = validate(package)
print("Package valid?", report.valid)
for row in report.flatten():
print(row)
```
**Output Example**:
```json
{
    "valid": false,
    "errors": [
        {"field": "Treatment", "message": "Value missing in row 2."},
        {"field": "Weight_20by100_cm", "message": "Value 'NA' is invalid."},
        {"field": "Site", "message": "Empty value detected in row 6."}
    ]
}
```
### 6. **How to Integrate Frictionless into the EnviDat Workflow**

#### 6.1 **Step 1: Researchers Check Data Quality**

* **Open Data Editor**: Researchers use the Open Data Editor to visually check their datasets. They can:

  * View validation errors.
  * Fix issues like missing values or incorrect data types.
  * Download the validated dataset.

#### 6.2 **Step 2: IT Staff Backend Validation**

* **Automated Validation**: Once the dataset is uploaded, IT staff can run a backend Python script using Frictionless to validate the data before it's stored in EnviDat.

  * The script can be integrated into the EnviDat upload process.

```python
from frictionless import Package

# Create a validation package for uploaded dataset
package = Package(resources=[{
    'name': 'ecological_data',
    'path': 'uploaded_data.csv',
    'schema': schema
}])

# Validate the package
package.validate()

# If valid, allow upload; if not, flag for corrections
if package.valid:
    print("Data is valid, ready to upload.")
else:
    print("Data has errors:", package.errors)
```
If, after running the custom schema, there are still errors, the dataset can be sent back to the researchers for correction with the helpful output from frictionless. 

### 7. **Conclusion**

By implementing **Frictionless**, WSL can streamline data quality assurance and control for EnviDat, empowering both researchers and IT staff:

* **Researchers**: Validate their datasets via the Open Data Editor, making corrections before upload.
* **IT Staff**: Automate backend validation with Python scripts to ensure that all incoming data complies with predefined quality standards.

**Next Steps**:

* Set up Frictionless in the EnviDat environment.
* Train researchers on how to use the Open Data Editor for self-checks.
* Automate backend validation using Frictionless Python scripts to ensure the integrity of all uploaded data.

**Online Resources**:

* https://framework.frictionlessdata.io/index.html
* https://colab.research.google.com/github/frictionlessdata/frictionless-py/blob/v4/site/docs/tutorials/notebooks/frictionless-RDM-workflows.ipynb#scrollTo=dc538394
### 1. **Introduction to the Frictionless Framework**

The **[Frictionless Framework](https://framework.frictionlessdata.io/)** offers [open-source tools](https://github.com/frictionlessdata) that help manage and ensure data quality. It’s ideal for use cases like **[EnviDat](https://www.envidat.ch/#/)**, where the integrity and reliability of data are critical for [long term storage and reuse](https://www.dora.lib4ri.ch/wsl/islandora/object/wsl:18703). It has been used successfully in similar repositories like [DRYAD](https://blog.datadryad.org/2020/11/18/frictionless-data/) and the [Global Biodiversity Information Facility (GBIF)](https://data-blog.gbif.org/post/frictionless-data-and-darwin-core/) for data validation and quality control.

### 2. **Big Picture: Why Frictionless for EnviDat?**

For **EnviDat**, quality assurance (QA) and control (QC) of uploaded ecological datasets is essential. Frictionless offers:

* **Flexibility**: Researchers can validate their own datasets using a graphical interface (**[Open Data Editor](https://okfn.org/en/projects/open-data-editor/)**) while SciIT staff can run backend checks through Python scripts.
* **Automates the Validation Process**: Ensures all incoming data fits the expected structure, types, and constraints prior to ingestion while freeing up staff for more complex tasks. 
* **Catches Common as well as Specific Errors**: Missing values, incorrect types, or malformed columns are standard, but common data error in ecological data can be added via a custom schema. 

### 3. **Example Dataset with Errors**

Let’s take a look at a **subsample of a real biomass dataset** uploaded to EnviDat, but we will introduce some intentional errors (missing values, blank headers, blank rows, NA's, data type error, etc.).

Original data (with no errors) come from _"Herbivory mediates the response of below-ground food-webs to invasive grasses"_, published in the _Journal of Animal Ecology_.
> _Fioratti, M., Cordero, I., Chinn, N., Firn, J., Holmes, J., Klein, M., Lebbink, G., Nielsen, U., Schütz, M., Zimmermann, S., Risch, A. C. (2025). Herbivory mediates the response of below-ground food-webs to invasive grasses. EnviDat. https://www.doi.org/10.16904/envidat.677._

```python
import pandas as pd
from pathlib import Path
from io import StringIO

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


# Load the dataset into pandas DataFrame
df = pd.read_csv(StringIO(csv_text))
df.head()  # Displaying the first few rows of the dataset
```
### 4. **Step-by-Step: How Frictionless Helps QC and QA**

#### 4.1 **Using the Open Data Editor (GUI) for QA**:

Researchers can use the **[Open Data Editor](https://okfn.org/en/projects/open-data-editor/)** to interactively validate their datasets before uploading them to EnviDat. The Open Data Editor provides a graphical interface that checks data quality in real-time.

* **What the Open Data Editor Can Catch**:

  * **Missing values** (e.g., "NA" entries in `Weight_20by100_cm` column).
  * **Incorrect data types** (e.g., text in numeric fields).
  * **Empty or missing columns**.
  * **Outliers** (values that fall outside the expected range).

#### Example: Fixing Missing Data in the Open Data Editor (GUI)

Researchers can open their dataset, visualize errors, and directly modify them in the GUI. If a field has missing values, users can choose to replace them with the average or a specific value.

#### 4.2 **Using Frictionless in Python for Backend Validation (QC)**:

Once the preliminary check has been done by the researchers, Scientific IT staff can run a Python script (or work in the console) to validate datasets automatically before upload. This is done by defining a custom **schema** that specifies the expected structure and rules for the dataset.

```python
# Install Frictionless Framework if necessary
!pip install frictionless
```
### 4.3 **What Errors Does the Default Schema Catch?**

* **Missing or null values** (e.g., NA in numerical fields).
* **Type mismatches** (e.g., text in numeric columns).
* **Invalid values** (e.g., `Invasion` should be either "Native" or "Invaded").
* **Duplicate rows** or columns.
* **Empty or missing headers**.

#### 4.4 **Custom Schema**:

You can **extend the default schema** to suit your own data structure. For example, you can set custom ranges for numeric columns, specific formats for strings, and define additional validation rules (e.g., a specific regex pattern for site names).

```python
from frictionless import Schema, Resource, validate

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

resource = Resource(path="biomass_sample.csv", schema=schema)
report = validate(resource)
print(report.valid)
```
**Output Example**:
```json
{'valid': False,
 'stats': {'tasks': 1, 'errors': 10, 'warnings': 0, 'seconds': 0.025},
 'warnings': [],
 'errors': [],
 'tasks': [{'name': 'biomass_sample',
            'type': 'table',
            'valid': False,
            'place': 'biomass_sample.csv',
            'labels': ['Site.ID',
                       'Biomasstype',
                       'Site',
                       'Invasion',
                       'Treatment',
                       'Weight_20by100_cm',
                       'sample_type'],
            'stats': {'errors': 10,
                      'warnings': 0,
                      'seconds': 0.025,
                      'md5': 'db2b1002484257d4cd39d5d3dd642178',
                      'sha256': 'f3ed66bb58831f187b6d4da8468ac5647cff259f18667abfea9381122663a351',
                      'bytes': 549,
                      'fields': 7,
                      'rows': 14},
            'warnings': [],
            'errors': [{'type': 'constraint-error',
                        'title': 'Constraint Error',
                        'description': 'A field value does not conform to a '
                                       'constraint.',
                        'message': 'The cell "" in row at position "5" and '
                                   'field "Invasion" at position "4" does not '
                                   'conform to a constraint: constraint '
                                   '"required" is "True"',
                        'tags': ['#table', '#row', '#cell'],
                        'note': 'constraint "required" is "True"',
                        'cells': ['2',
                                  'Living',
                                  'PnK',
                                  '',
                                  'No livestock',
                                  '177.355',
                                  ''],
                        'rowNumber': 5,
                        'cell': '',
                        'fieldName': 'Invasion',
                        'fieldNumber': 4},
                       {'type': 'type-error',
                        'title': 'Type Error',
                        'description': 'The value does not match the schema '
                                       'type and format for this field.',
                        'message': 'Type error in the cell "error" in row "7" '
                                   'and field "Site.ID" at position "1": type '
                                   'is "integer/default"',
                        'tags': ['#table', '#row', '#cell'],
                        'note': 'type is "integer/default"',
                        'cells': ['error',
                                  'Living',
                                  'PnK',
                                  'Native',
                                  'No mammals',
                                  '117.16',
                                  ''],
                        'rowNumber': 7,
                        'cell': 'error',
                        'fieldName': 'Site.ID',
                        'fieldNumber': 1},
                       {'type': 'blank-row',
                        'title': 'Blank Row',
                        'description': 'This row is empty. A row should '
                                       'contain at least one value.',
                        'message': 'Row at position "8" is completely blank',
                        'tags': ['#table', '#row'],
                        'note': '',
                        'cells': ['', '', '', '', '', '', ''],
                        'rowNumber': 8},
                       {'type': 'constraint-error',
                        'title': 'Constraint Error',
                        'description': 'A field value does not conform to a '
                                       'constraint.',
                        'message': 'The cell "" in row at position "9" and '
                                   'field "Site.ID" at position "1" does not '
                                   'conform to a constraint: constraint '
                                   '"required" is "True"',
                        'tags': ['#table', '#row', '#cell'],
                        'note': 'constraint "required" is "True"',
                        'cells': ['', '', '', '', '', '', 'red'],
                        'rowNumber': 9,
                        'cell': '',
                        'fieldName': 'Site.ID',
                        'fieldNumber': 1},
                       {'type': 'constraint-error',
                        'title': 'Constraint Error',
                        'description': 'A field value does not conform to a '
                                       'constraint.',
                        'message': 'The cell "" in row at position "9" and '
                                   'field "Biomasstype" at position "2" does '
                                   'not conform to a constraint: constraint '
                                   '"required" is "True"',
                        'tags': ['#table', '#row', '#cell'],
                        'note': 'constraint "required" is "True"',
                        'cells': ['', '', '', '', '', '', 'red'],
                        'rowNumber': 9,
                        'cell': '',
                        'fieldName': 'Biomasstype',
                        'fieldNumber': 2},
                       {'type': 'constraint-error',
                        'title': 'Constraint Error',
                        'description': 'A field value does not conform to a '
                                       'constraint.',
                        'message': 'The cell "" in row at position "9" and '
                                   'field "Site" at position "3" does not '
                                   'conform to a constraint: constraint '
                                   '"required" is "True"',
                        'tags': ['#table', '#row', '#cell'],
                        'note': 'constraint "required" is "True"',
                        'cells': ['', '', '', '', '', '', 'red'],
                        'rowNumber': 9,
                        'cell': '',
                        'fieldName': 'Site',
                        'fieldNumber': 3},
                       {'type': 'constraint-error',
                        'title': 'Constraint Error',
                        'description': 'A field value does not conform to a '
                                       'constraint.',
                        'message': 'The cell "" in row at position "9" and '
                                   'field "Invasion" at position "4" does not '
                                   'conform to a constraint: constraint '
                                   '"required" is "True"',
                        'tags': ['#table', '#row', '#cell'],
                        'note': 'constraint "required" is "True"',
                        'cells': ['', '', '', '', '', '', 'red'],
                        'rowNumber': 9,
                        'cell': '',
                        'fieldName': 'Invasion',
                        'fieldNumber': 4},
                       {'type': 'constraint-error',
                        'title': 'Constraint Error',
                        'description': 'A field value does not conform to a '
                                       'constraint.',
                        'message': 'The cell "" in row at position "9" and '
                                   'field "Treatment" at position "5" does not '
                                   'conform to a constraint: constraint '
                                   '"required" is "True"',
                        'tags': ['#table', '#row', '#cell'],
                        'note': 'constraint "required" is "True"',
                        'cells': ['', '', '', '', '', '', 'red'],
                        'rowNumber': 9,
                        'cell': '',
                        'fieldName': 'Treatment',
                        'fieldNumber': 5},
                       {'type': 'constraint-error',
                        'title': 'Constraint Error',
                        'description': 'A field value does not conform to a '
                                       'constraint.',
                        'message': 'The cell "" in row at position "9" and '
                                   'field "Weight_20by100_cm" at position "6" '
                                   'does not conform to a constraint: '
                                   'constraint "required" is "True"',
                        'tags': ['#table', '#row', '#cell'],
                        'note': 'constraint "required" is "True"',
                        'cells': ['', '', '', '', '', '', 'red'],
                        'rowNumber': 9,
                        'cell': '',
                        'fieldName': 'Weight_20by100_cm',
                        'fieldNumber': 6},
                       {'type': 'constraint-error',
                        'title': 'Constraint Error',
                        'description': 'A field value does not conform to a '
                                       'constraint.',
                        'message': 'The cell "NA" in row at position "10" and '
                                   'field "Weight_20by100_cm" at position "6" '
                                   'does not conform to a constraint: '
                                   'constraint "required" is "True"',
                        'tags': ['#table', '#row', '#cell'],
                        'note': 'constraint "required" is "True"',
                        'cells': ['9',
                                  'Litter',
                                  'Vivan',
                                  'Native',
                                  'Open',
                                  'NA',
                                  ''],
                        'rowNumber': 10,
                        'cell': 'NA',
                        'fieldName': 'Weight_20by100_cm',
                        'fieldNumber': 6}]}]}
```
### 5. **How to Integrate Frictionless into the EnviDat Workflow**

#### 5.1 **Step 2: IT Staff Backend Validation**

* **Automated Validation**: Once the dataset is uploaded, a Python script using Frictionless to validate the data before it's stored in EnviDat. This could use one official EnviDat schema, or could be a collection of schema depending on the data type. 

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

#### 6.  **automated cracking of iCSV/NEAD files**: since WSL is pioneering self-documented CSV's, we can take advantage of the extra information in an automated process

### 7. **Conclusion**

By implementing **Frictionless**, WSL can streamline data quality assurance and control for EnviDat, empowering both researchers and IT staff:

* **Researchers**: Validate their datasets via the Open Data Editor, making corrections before upload.
* **IT Staff**: Automate backend validation with Python scripts to ensure that all incoming data complies with predefined quality standards.

**Next Steps**:

* Set up Frictionless in the EnviDat environment.
* Train researchers on how to use the Open Data Editor for self-checks.

**Online Resources**:

* https://framework.frictionlessdata.io/index.html
* https://colab.research.google.com/github/frictionlessdata/frictionless-py/blob/v4/site/docs/tutorials/notebooks/frictionless-RDM-workflows.ipynb#scrollTo=dc538394
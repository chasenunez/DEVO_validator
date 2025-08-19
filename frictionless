from pprint import pprint
from frictionless import Checklist, validate

checklist = Checklist()
pprint(checklist.scope)
report = validate('capital-invalid.csv')  # we don't pass the checklist as the empty one is default
pprint(report.flatten(['type', 'message']))
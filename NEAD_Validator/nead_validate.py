#!/usr/bin/env python3
"""
nead_validate.py: Wrapper to run full NEAD/iCSV validation pipeline
on one or more input files.

Usage:
    python3 nead_validate.py file1.icsv file2.icsv ...
"""

import sys
import subprocess
from pathlib import Path

def run_step(script, infile):
    """Run a step script with a given input file"""
    result = subprocess.run(
        ["python3", script, infile],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"❌ {script} failed on {infile}")
        print(result.stdout)
        print(result.stderr)
        return False
    print(f"✅ {script} succeeded on {infile}")
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 nead_validate.py file1.icsv [file2.icsv ...]")
        sys.exit(1)

    scripts = ["check_metadata.py", "create_schema.py", "validate_data.py"]

    for infile in sys.argv[1:]:
        if not Path(infile).exists():
            print(f"⚠️  Skipping {infile}: file not found")
            continue

        print("\n===============================")
        print(f"Processing {infile}")
        print("===============================")

        for script in scripts:
            ok = run_step(script, infile)
            if not ok:
                print(f"Stopping pipeline for {infile} due to errors.")
                break

if __name__ == "__main__":
    main()

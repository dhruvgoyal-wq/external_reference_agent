#!/usr/bin/env python3
"""
Master script to insert all data into the ext_reference database
Runs all insertion scripts in sequence
"""

import subprocess
import sys
from pathlib import Path


def run_script(script_name, description):
    """Run a Python script and return success status"""
    print("\n" + "="*70)
    print(f"RUNNING: {description}")
    print("="*70)

    script_path = Path(__file__).parent / script_name

    if not script_path.exists():
        print(f"ERROR: Script not found - {script_path}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            text=True
        )

        if result.returncode == 0:
            print(f"\n✓ {description} - COMPLETED SUCCESSFULLY")
            return True
        else:
            print(f"\n✗ {description} - FAILED (exit code: {result.returncode})")
            return False

    except Exception as err:
        print(f"\n✗ {description} - ERROR: {err}")
        return False


def main():
    """Run all insertion scripts in sequence"""
    print("="*70)
    print("EXT REFERENCE DATABASE - BULK DATA INSERTION")
    print("="*70)
    print("This script will insert data into the following tables:")
    print("  1. fact_country_risk_registry")
    print("  2. fact_federal_holidays")
    print("  3. fact_benchmark_rates")
    print("="*70)

    input("\nPress Enter to begin, or Ctrl+C to cancel...")

    scripts = [
        {
            "file": "insert_country_risk_registry.py",
            "description": "Country Risk Registry Data"
        },
        {
            "file": "insert_federal_holidays.py",
            "description": "Federal Holidays Data (USA, CAN, GBR)"
        },
        {
            "file": "insert_benchmark_rates.py",
            "description": "Benchmark Rates Data (Prime, Overnight, etc.)"
        }
    ]

    results = []

    for script in scripts:
        success = run_script(script["file"], script["description"])
        results.append({
            "description": script["description"],
            "success": success
        })

    # Print final summary
    print("\n\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)

    all_success = True
    for i, result in enumerate(results, 1):
        status = "✓ SUCCESS" if result["success"] else "✗ FAILED"
        print(f"{i}. {result['description']}: {status}")
        if not result["success"]:
            all_success = False

    print("="*70)

    if all_success:
        print("\n🎉 All data insertions completed successfully!")
        return 0
    else:
        print("\n⚠️  Some insertions failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)

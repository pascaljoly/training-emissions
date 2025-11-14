#!/usr/bin/env python3
"""
Data Source Update Script

Automatically updates GPU specifications and provides guidance for updating
carbon intensity data from authoritative sources.
"""

import json
import argparse
import shutil
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError, HTTPError


# Data source URLs
GPU_DATA_URL = "https://raw.githubusercontent.com/voidful/gpu-info-api/gpu-data/gpu.json"


def create_backup(file_path):
    """Create a timestamped backup of a file."""
    if not Path(file_path).exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    print(f"  ✓ Created backup: {backup_path}")
    return backup_path


def fetch_json(url, timeout=10):
    """Fetch JSON data from a URL."""
    try:
        with urlopen(url, timeout=timeout) as response:
            data = response.read()
            return json.loads(data)
    except HTTPError as e:
        print(f"  ✗ HTTP Error {e.code}: {e.reason}")
        return None
    except URLError as e:
        print(f"  ✗ URL Error: {e.reason}")
        return None
    except json.JSONDecodeError as e:
        print(f"  ✗ JSON decode error: {e}")
        return None
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        return None


def extract_nvidia_gpus(gpu_data):
    """Extract NVIDIA datacenter GPU specifications from the source data."""
    nvidia_gpus = {}

    # Target NVIDIA datacenter GPUs
    target_models = ['A100', 'A100-80GB', 'H100', 'V100', 'T4', 'A10', 'A40', 'L4', 'L40', 'L40S']

    for gpu_name, gpu_info in gpu_data.items():
        # Look for NVIDIA datacenter GPUs
        if not isinstance(gpu_info, dict):
            continue

        # Check if this is a target GPU model
        gpu_model = None
        for target in target_models:
            if target in gpu_name:
                gpu_model = target
                break

        if not gpu_model:
            continue

        # Extract TDP (try different field names)
        tdp = None
        if 'TDP (Watts)' in gpu_info:
            try:
                tdp = int(gpu_info['TDP (Watts)'])
            except (ValueError, TypeError):
                continue

        if tdp is None:
            continue

        # Extract memory if available
        memory = None
        if 'Memory (GB)' in gpu_info:
            try:
                memory = int(gpu_info['Memory (GB)'])
            except (ValueError, TypeError):
                pass

        # Store GPU info
        if gpu_model not in nvidia_gpus or (memory and '80' in gpu_model and memory >= 80):
            nvidia_gpus[gpu_model] = {
                'name': f"NVIDIA {gpu_model}",
                'tdp_watts': tdp,
                'vendor': 'NVIDIA',
                'memory_gb': memory if memory else 'Unknown',
                'notes': f"Datacenter GPU - Updated from voidful/gpu-info-api"
            }

    return nvidia_gpus


def update_gpu_specs(dry_run=False):
    """Update GPU specifications from online source."""
    print("\n" + "="*80)
    print("UPDATING GPU SPECIFICATIONS")
    print("="*80 + "\n")

    script_dir = Path(__file__).parent
    gpu_specs_file = script_dir / 'gpu_specs.json'

    # Load current GPU specs
    print("Loading current GPU specifications...")
    try:
        with open(gpu_specs_file, 'r') as f:
            current_specs = json.load(f)
        print(f"  ✓ Loaded {len(current_specs)} current GPU models\n")
    except FileNotFoundError:
        print("  ! gpu_specs.json not found, will create new file\n")
        current_specs = {}
    except json.JSONDecodeError as e:
        print(f"  ✗ Error reading current specs: {e}")
        return False

    # Fetch new GPU data
    print(f"Fetching GPU data from voidful/gpu-info-api...")
    print(f"  URL: {GPU_DATA_URL}")
    gpu_data = fetch_json(GPU_DATA_URL)

    if not gpu_data:
        print("\n✗ Failed to fetch GPU data")
        return False

    print(f"  ✓ Fetched data for {len(gpu_data)} GPUs\n")

    # Extract NVIDIA datacenter GPUs
    print("Extracting NVIDIA datacenter GPU specifications...")
    new_specs = extract_nvidia_gpus(gpu_data)
    print(f"  ✓ Extracted {len(new_specs)} NVIDIA datacenter GPUs\n")

    if not new_specs:
        print("✗ No GPU data extracted")
        return False

    # Compare and show changes
    print("Comparing with current specifications...")
    added = []
    updated = []
    unchanged = []

    for model, specs in new_specs.items():
        if model not in current_specs:
            added.append(model)
        elif current_specs[model].get('tdp_watts') != specs['tdp_watts']:
            updated.append((model, current_specs[model]['tdp_watts'], specs['tdp_watts']))
        else:
            unchanged.append(model)

    # Show summary
    print(f"\n  New GPUs: {len(added)}")
    if added:
        for model in added:
            print(f"    + {model}: {new_specs[model]['tdp_watts']}W")

    print(f"\n  Updated GPUs: {len(updated)}")
    if updated:
        for model, old_tdp, new_tdp in updated:
            print(f"    • {model}: {old_tdp}W → {new_tdp}W")

    print(f"\n  Unchanged GPUs: {len(unchanged)}")

    # Merge with current specs (preserve any custom entries)
    merged_specs = {**current_specs, **new_specs}

    if dry_run:
        print("\n[DRY RUN] No changes written to disk")
        print(f"Would update {gpu_specs_file}")
        return True

    # Create backup
    print("\nCreating backup...")
    create_backup(gpu_specs_file)

    # Write updated specs
    print("\nWriting updated specifications...")
    with open(gpu_specs_file, 'w') as f:
        json.dump(merged_specs, f, indent=2)

    print(f"  ✓ Updated {gpu_specs_file}")
    print(f"  ✓ Total GPUs in database: {len(merged_specs)}")

    return True


def show_carbon_intensity_guidance():
    """Show guidance for updating carbon intensity data."""
    print("\n" + "="*80)
    print("CARBON INTENSITY DATA UPDATE GUIDANCE")
    print("="*80 + "\n")

    print("Carbon intensity data should be updated from these authoritative sources:\n")

    print("1. Cloud Carbon Footprint (CCF)")
    print("   Repository: https://github.com/cloud-carbon-footprint/cloud-carbon-coefficients")
    print("   License: Apache 2.0")
    print("   Data: coefficients-aws-use.csv, coefficients-gcp-use.csv, coefficients-azure-use.csv")
    print("   Field: 'GridEmissionsFactor' (kg CO2e per kWh)\n")

    print("2. EPA eGRID (US Regions)")
    print("   URL: https://www.epa.gov/egrid/download-data")
    print("   Data: eGRID Year Data (Excel/CSV)")
    print("   Field: 'NERC Region' carbon intensity (lb CO2/MWh, convert to kg/kWh)\n")

    print("3. Cloud Provider Sustainability Reports")
    print("   - Google Cloud: https://cloud.google.com/sustainability/region-carbon")
    print("   - Microsoft Azure: https://www.microsoft.com/en-us/sustainability")
    print("   - AWS: Check regional sustainability data pages\n")

    print("4. electricityMap API (real-time data)")
    print("   URL: https://api.electricitymap.org/")
    print("   Note: Requires API key, provides real-time carbon intensity by zone\n")

    print("To update carbon_intensity.json:")
    print("  1. Download data from the sources above")
    print("  2. Extract carbon intensity values (kg CO2 per kWh)")
    print("  3. Manually update carbon_intensity.json with new values")
    print("  4. Document the source and date in the 'notes' field")
    print("\nExample format:")
    print("""  {
    "us-east-1": {
      "region_name": "US East (N. Virginia)",
      "kg_co2_per_kwh": 0.448,
      "provider": "AWS",
      "notes": "EPA eGRID 2022 data, updated 2025-11"
    }
  }""")

    print("\nNote: Carbon intensity values change over time as grids add more renewables.")
    print("      Recommend updating annually or when new data is published.")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Update GPU and carbon intensity data from authoritative sources',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update GPU specifications
  python3 update_data_sources.py --gpu

  # Show carbon intensity update guidance
  python3 update_data_sources.py --carbon

  # Update all (GPU + show carbon guidance)
  python3 update_data_sources.py --all

  # Dry run (show what would change without updating)
  python3 update_data_sources.py --gpu --dry-run
        """
    )

    parser.add_argument(
        '--gpu',
        action='store_true',
        help='Update GPU specifications from voidful/gpu-info-api'
    )
    parser.add_argument(
        '--carbon',
        action='store_true',
        help='Show guidance for updating carbon intensity data'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Update GPU specs and show carbon guidance'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would change without writing to disk'
    )

    args = parser.parse_args()

    # If no arguments, show help
    if not (args.gpu or args.carbon or args.all):
        parser.print_help()
        return

    success = True

    # Update GPU specs
    if args.gpu or args.all:
        success = update_gpu_specs(dry_run=args.dry_run)

    # Show carbon intensity guidance
    if args.carbon or args.all:
        show_carbon_intensity_guidance()

    # Summary
    print("\n" + "="*80)
    if success:
        print("✓ Data source update completed successfully")
    else:
        print("✗ Data source update encountered errors")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()

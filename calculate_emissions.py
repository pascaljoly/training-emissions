#!/usr/bin/env python3
"""
ML Training Emissions Calculator

Calculates energy consumption and CO2 emissions from ML training runs
based on GPU specifications, utilization, duration, and regional carbon intensity.
"""

import json
import csv
import os
import argparse
from datetime import datetime
from pathlib import Path


def load_json(filename):
    """Load and parse a JSON file."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{filename}': {e}")
        exit(1)


def validate_run(run, run_idx):
    """Validate run parameters."""
    errors = []

    # Required fields
    required_fields = ['run_name', 'gpu_model', 'gpu_count', 'duration_hours', 'utilization', 'region', 'pue']
    for field in required_fields:
        if field not in run:
            errors.append(f"Missing required field '{field}'")

    if errors:
        return errors

    # Utilization validation (0-1)
    if not (0 <= run['utilization'] <= 1):
        errors.append(f"Utilization must be between 0 and 1 (got {run['utilization']})")

    # Duration validation (>0)
    if run['duration_hours'] <= 0:
        errors.append(f"Duration must be greater than 0 (got {run['duration_hours']})")

    # GPU count validation (>0)
    if run['gpu_count'] <= 0:
        errors.append(f"GPU count must be greater than 0 (got {run['gpu_count']})")

    # PUE validation (>=1.0)
    if run['pue'] < 1.0:
        errors.append(f"PUE must be >= 1.0 (got {run['pue']})")

    return errors


def calculate_emissions(run, gpu_specs, carbon_intensity):
    """Calculate energy consumption and emissions for a training run."""

    # Lookup GPU TDP
    gpu_model = run['gpu_model']
    if gpu_model not in gpu_specs:
        raise ValueError(f"GPU model '{gpu_model}' not found in gpu_specs.json. Available: {', '.join(gpu_specs.keys())}")

    gpu_tdp_watts = gpu_specs[gpu_model]['tdp_watts']

    # Lookup carbon intensity
    region = run['region']
    if region not in carbon_intensity:
        raise ValueError(f"Region '{region}' not found in carbon_intensity.json. Available: {', '.join(carbon_intensity.keys())}")

    carbon_kg_per_kwh = carbon_intensity[region]['kg_co2_per_kwh']

    # Calculate energy consumption (GPU only)
    # energy_kwh = (watts × count × hours × utilization) / 1000
    energy_gpu_kwh = (
        gpu_tdp_watts *
        run['gpu_count'] *
        run['duration_hours'] *
        run['utilization']
    ) / 1000

    # Apply PUE for total datacenter energy
    energy_total_kwh = energy_gpu_kwh * run['pue']

    # Calculate emissions
    emissions_kg_co2 = energy_total_kwh * carbon_kg_per_kwh

    return {
        'run_name': run['run_name'],
        'timestamp': datetime.now().isoformat(),
        'gpu_model': gpu_model,
        'gpu_count': run['gpu_count'],
        'duration_hours': run['duration_hours'],
        'utilization': run['utilization'],
        'region': region,
        'carbon_intensity_kg_co2_kwh': carbon_kg_per_kwh,
        'pue': run['pue'],
        'energy_gpu_kwh': round(energy_gpu_kwh, 4),
        'energy_total_kwh': round(energy_total_kwh, 4),
        'emissions_kg_co2': round(emissions_kg_co2, 4)
    }


def save_to_csv(results, filename='emissions.csv'):
    """Append results to CSV file."""

    fieldnames = [
        'run_name', 'timestamp', 'gpu_model', 'gpu_count', 'duration_hours',
        'utilization', 'region', 'carbon_intensity_kg_co2_kwh', 'pue',
        'energy_gpu_kwh', 'energy_total_kwh', 'emissions_kg_co2'
    ]

    # Create output directory if it doesn't exist
    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if file exists to determine if we need to write header
    file_exists = os.path.isfile(filename)

    with open(filename, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for result in results:
            writer.writerow(result)


def print_summary(results):
    """Print summary of emissions calculations to console."""

    print("\n" + "="*80)
    print("ML TRAINING EMISSIONS CALCULATION RESULTS")
    print("="*80 + "\n")

    total_emissions = 0
    total_energy = 0

    for i, result in enumerate(results, 1):
        print(f"Run {i}: {result['run_name']}")
        print(f"  GPU: {result['gpu_count']}x {result['gpu_model']}")
        print(f"  Duration: {result['duration_hours']} hours @ {result['utilization']*100}% utilization")
        print(f"  Region: {result['region']} (Carbon intensity: {result['carbon_intensity_kg_co2_kwh']} kg CO₂/kWh)")
        print(f"  PUE: {result['pue']}")
        print(f"  Energy (GPU only): {result['energy_gpu_kwh']} kWh")
        print(f"  Energy (Total with PUE): {result['energy_total_kwh']} kWh")
        print(f"  Emissions: {result['emissions_kg_co2']} kg CO₂")
        print()

        total_emissions += result['emissions_kg_co2']
        total_energy += result['energy_total_kwh']

    print("-"*80)
    print(f"TOTAL ACROSS ALL RUNS:")
    print(f"  Total Energy: {round(total_energy, 4)} kWh")
    print(f"  Total Emissions: {round(total_emissions, 4)} kg CO₂")
    print(f"  Equivalent to: {round(total_emissions/1000, 4)} metric tons CO₂")
    print("="*80 + "\n")


def main():
    """Main execution function."""

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Calculate energy consumption and CO2 emissions from ML training runs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default output file (emissions.csv)
  python3 calculate_emissions.py

  # Specify custom output file
  python3 calculate_emissions.py -o my_results.csv

  # Specify output file in custom directory
  python3 calculate_emissions.py --output results/2025/january_training.csv
        """
    )
    parser.add_argument(
        '-o', '--output',
        default='emissions.csv',
        help='Output CSV file path (default: emissions.csv). Directory will be created if it does not exist.'
    )
    args = parser.parse_args()

    # Get script directory
    script_dir = Path(__file__).parent

    # Load configuration files
    print("Loading configuration files...")
    gpu_specs = load_json(script_dir / 'gpu_specs.json')
    carbon_intensity = load_json(script_dir / 'carbon_intensity.json')
    parameters = load_json(script_dir / 'parameters.json')

    if 'runs' not in parameters:
        print("Error: 'runs' key not found in parameters.json")
        exit(1)

    runs = parameters['runs']
    print(f"Found {len(runs)} training run(s) to process.\n")

    # Validate and calculate emissions for each run
    results = []

    for idx, run in enumerate(runs, 1):
        print(f"Processing run {idx}/{len(runs)}: {run.get('run_name', 'unnamed')}...")

        # Validate run parameters
        validation_errors = validate_run(run, idx)
        if validation_errors:
            print(f"  Error: Invalid parameters for run {idx}:")
            for error in validation_errors:
                print(f"    - {error}")
            continue

        # Calculate emissions
        try:
            result = calculate_emissions(run, gpu_specs, carbon_intensity)
            results.append(result)
            print(f"  ✓ Calculated: {result['emissions_kg_co2']} kg CO₂")
        except ValueError as e:
            print(f"  Error: {e}")
            continue

    if not results:
        print("\nNo valid runs to process. Exiting.")
        exit(1)

    # Save results to CSV
    csv_filename = args.output
    print(f"\nSaving results to {csv_filename}...")
    save_to_csv(results, csv_filename)
    print("✓ Results saved successfully")

    # Print summary
    print_summary(results)


if __name__ == '__main__':
    main()

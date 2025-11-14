# ML Training Emissions Calculator

Calculate energy consumption and CO₂ emissions from machine learning training runs based on GPU specifications, utilization, duration, and regional carbon intensity.

## Overview

This tool helps you estimate the environmental impact of ML model training by calculating:
- **Energy consumption** (kWh) from GPU usage
- **Total datacenter energy** including PUE (Power Usage Effectiveness)
- **CO₂ emissions** (kg) based on regional grid carbon intensity

## Quick Start

1. **Edit `parameters.json`** with your training run details
2. **Run the calculator**:
   ```bash
   python3 calculate_emissions.py
   ```
3. **View results** in console output and `emissions.csv`

## Files

### Configuration Files

- **`gpu_specs.json`** - GPU models and their TDP (Thermal Design Power) specifications
  - Includes: A100, H100, V100, T4, A10
  - Add custom GPUs as needed

- **`carbon_intensity.json`** - Regional carbon intensity values (kg CO₂/kWh)
  - Includes: Major AWS/GCP/Azure regions
  - Values based on regional grid mix

- **`parameters.json`** - Your training run configurations
  - Edit this file to add/modify runs

### Scripts

- **`calculate_emissions.py`** - Main calculation script

### Output

- **`emissions.csv`** - Cumulative results (appends on each run)

## Usage

### 1. Configure Your Training Runs

Edit `parameters.json`:

```json
{
  "runs": [
    {
      "run_name": "my_model_training",
      "gpu_model": "A100",
      "gpu_count": 8,
      "duration_hours": 48,
      "utilization": 0.80,
      "region": "us-west-2",
      "pue": 1.2
    }
  ]
}
```

**Parameters:**
- `run_name`: Descriptive name for this training run
- `gpu_model`: GPU type (must exist in `gpu_specs.json`)
- `gpu_count`: Number of GPUs used
- `duration_hours`: Training duration in hours
- `utilization`: GPU utilization (0.0-1.0, where 1.0 = 100%)
- `region`: Cloud region (must exist in `carbon_intensity.json`)
- `pue`: Power Usage Effectiveness (typically 1.1-1.6, default 1.2)

### 2. Run the Calculator

```bash
python3 calculate_emissions.py
```

### 3. View Results

**Console output** shows detailed breakdown:
```
Run 1: my_model_training
  GPU: 8x A100
  Duration: 48 hours @ 80.0% utilization
  Region: us-west-2 (Carbon intensity: 0.285 kg CO₂/kWh)
  PUE: 1.2
  Energy (GPU only): 122.88 kWh
  Energy (Total with PUE): 147.456 kWh
  Emissions: 42.0249 kg CO₂
```

**CSV file** (`emissions.csv`) contains all runs with timestamp for tracking over time.

## Calculation Method

### Energy Consumption

**GPU Energy (kWh):**
```
energy_gpu_kwh = (gpu_tdp_watts × gpu_count × duration_hours × utilization) / 1000
```

**Total Datacenter Energy (kWh):**
```
energy_total_kwh = energy_gpu_kwh × pue
```

### CO₂ Emissions

```
emissions_kg_co2 = energy_total_kwh × carbon_intensity_kg_co2_kwh
```

## Adding Custom Configurations

### Add a GPU Model

Edit `gpu_specs.json`:
```json
{
  "RTX-4090": {
    "name": "NVIDIA RTX 4090",
    "tdp_watts": 450,
    "memory_gb": 24,
    "notes": "Consumer GPU"
  }
}
```

### Add a Region

Edit `carbon_intensity.json`:
```json
{
  "eu-central-1": {
    "region_name": "EU Central (Frankfurt)",
    "kg_co2_per_kwh": 0.338,
    "notes": "German grid mix"
  }
}
```

## Understanding Results

### Energy Metrics
- **Energy (GPU only)**: Raw GPU power consumption
- **Energy (Total with PUE)**: Includes datacenter overhead (cooling, networking, etc.)

### Carbon Intensity
Carbon intensity varies significantly by region:
- **Low (<0.1)**: Hydro/nuclear heavy (Switzerland, Norway)
- **Medium (0.2-0.4)**: Mixed renewable/fossil (US West, EU West)
- **High (>0.5)**: Coal heavy (Asia, Australia)

### PUE (Power Usage Effectiveness)
- **1.0**: Theoretical perfect efficiency (impossible)
- **1.1-1.2**: Excellent (hyperscale datacenters)
- **1.3-1.5**: Good (modern facilities)
- **1.5-2.0**: Typical (older facilities)

## Validation

The script validates:
- ✓ Utilization is between 0 and 1
- ✓ Duration is greater than 0
- ✓ GPU count is greater than 0
- ✓ PUE is at least 1.0
- ✓ GPU model exists in specifications
- ✓ Region exists in carbon intensity data

Invalid runs are skipped with clear error messages.

## Example Output

Running the sample `parameters.json`:

```
TOTAL ACROSS ALL RUNS:
  Total Energy: 90.756 kWh
  Total Emissions: 22.6239 kg CO₂
  Equivalent to: 0.0226 metric tons CO₂
```

**Context:** 22.6 kg CO₂ is approximately:
- 90 miles driven in an average passenger car
- 10 kg of coal burned
- 2.5 gallons of gasoline

## Dependencies

- **Python 3.6+**
- **Standard library only** (json, csv, datetime, pathlib, os)

No external packages required!

## License

MIT License - See main repository LICENSE file

## Author

Pascal Joly - IT Climate Ed, LLC

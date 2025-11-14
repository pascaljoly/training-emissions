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

**Custom output file:**
```bash
# Specify a custom output file
python3 calculate_emissions.py -o my_results.csv

# Save to a custom directory
python3 calculate_emissions.py --output results/2025/january_training.csv
```

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
- **`update_data_sources.py`** - Data source update utility (see [Updating Data Sources](#updating-data-sources))

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

**Basic usage** (saves to `emissions.csv`):
```bash
python3 calculate_emissions.py
```

**Custom output file:**
```bash
# Specify custom file name
python3 calculate_emissions.py -o my_results.csv

# Save to custom directory (directory will be created if needed)
python3 calculate_emissions.py --output results/2025/january_training.csv
```

**Command-line options:**
- `-o`, `--output`: Specify output CSV file path (default: `emissions.csv`)
- `-h`, `--help`: Show help message with all options

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
    "vendor": "NVIDIA",
    "memory_gb": 24,
    "notes": "Consumer GPU"
  }
}
```

**Required fields:**
- `tdp_watts`: Thermal Design Power in watts
- `vendor`: Manufacturer name

**Optional fields:**
- `name`: Full descriptive name
- `memory_gb`: GPU memory capacity
- `notes`: Additional information

### Add a Region

Edit `carbon_intensity.json`:
```json
{
  "eu-central-1": {
    "region_name": "EU Central (Frankfurt)",
    "kg_co2_per_kwh": 0.338,
    "provider": "AWS",
    "notes": "German grid mix"
  }
}
```

**Required fields:**
- `kg_co2_per_kwh`: Carbon intensity value
- `provider`: Cloud provider (AWS/GCP/Azure) or "On-Premise"

**Optional fields:**
- `region_name`: Descriptive location name
- `notes`: Data source or additional context

## Updating Data Sources

The repository includes `update_data_sources.py` to help refresh GPU specifications and carbon intensity data from authoritative sources.

### Update GPU Specifications

Automatically fetch updated GPU TDP values from the voidful/gpu-info-api repository:

```bash
# Preview changes without modifying files
python3 update_data_sources.py --gpu --dry-run

# Update GPU specifications
python3 update_data_sources.py --gpu
```

The script will:
- Fetch latest GPU data from [voidful/gpu-info-api](https://github.com/voidful/gpu-info-api)
- Extract NVIDIA datacenter GPU specifications
- Create a timestamped backup of `gpu_specs.json`
- Show what changed (new GPUs, updated TDP values)
- Update the local `gpu_specs.json` file

**Note:** Always run with `--dry-run` first to review changes. GPU TDP can vary by variant, so manually verify values before using them in production calculations.

### Update Carbon Intensity Data

View guidance for updating carbon intensity from authoritative sources:

```bash
python3 update_data_sources.py --carbon
```

This displays:
- Links to authoritative data sources (Cloud Carbon Footprint, EPA eGRID, cloud providers)
- Instructions for extracting values
- Example format for updating `carbon_intensity.json`
- Recommended update frequency

**Carbon intensity sources:**
1. **Cloud Carbon Footprint** - [cloud-carbon-coefficients](https://github.com/cloud-carbon-footprint/cloud-carbon-coefficients)
2. **EPA eGRID** - [Download data](https://www.epa.gov/egrid/download-data)
3. **Google Cloud** - [Region carbon data](https://cloud.google.com/sustainability/region-carbon)
4. **electricityMap API** - [API documentation](https://api.electricitymap.org/)

**Recommended update frequency:**
- Carbon intensity: Annually or when new grid data is published
- GPU specifications: When new GPU models are released or TDP values are revised

### Update All Data Sources

Run both GPU update and show carbon guidance:

```bash
python3 update_data_sources.py --all
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

## Data Sources and Methodology

### GPU TDP Data

GPU Thermal Design Power (TDP) specifications are sourced from:
- **Primary source**: [voidful/gpu-info-api](https://github.com/voidful/gpu-info-api) - Open source GPU database
- **Manual verification**: NVIDIA official specifications and datasheets
- **Field extracted**: `"TDP (Watts)"` for each GPU model

To add new GPUs, reference the GPU database API or manufacturer specifications.

### Carbon Intensity Data

Regional carbon intensity values (kg CO₂/kWh) are sourced from:

1. **Cloud Carbon Footprint (CCF)**
   - Repository: [cloud-carbon-coefficients](https://github.com/cloud-carbon-footprint/cloud-carbon-coefficients)
   - License: Apache 2.0
   - Methodology: Combines EPA eGRID data with cloud provider PUE values

2. **US Regions**
   - Source: EPA eGRID 2020 (Emissions & Generation Resource Integrated Database)
   - NERC region-based carbon intensity factors
   - Updated annually by EPA

3. **Cloud Provider Reports**
   - Google Cloud: [Sustainability reports](https://cloud.google.com/sustainability)
   - Microsoft Azure: [Emissions Impact Dashboard](https://www.microsoft.com/en-us/sustainability)
   - AWS: Regional grid mix data

### Methodology References

This calculator follows the methodology described in:
- **"Energy and Policy Considerations for Deep Learning in NLP"** (Strubell et al., 2019)
- **Cloud Carbon Footprint Methodology** - [Documentation](https://www.cloudcarbonfootprint.org/docs/methodology/)
- **Green Software Foundation** - [Software Carbon Intensity (SCI) Specification](https://greensoftware.foundation/)

**Formula:**
```
Total Emissions = GPU Energy × PUE × Grid Carbon Intensity

Where:
- GPU Energy = TDP × GPU Count × Duration × Utilization
- PUE = Power Usage Effectiveness (datacenter efficiency)
- Grid Carbon Intensity = kg CO₂ per kWh (regional grid mix)
```

### Limitations and Assumptions

1. **TDP vs Actual Power**: Uses TDP as proxy for actual power draw. Real consumption varies with workload.
2. **Static Carbon Intensity**: Uses average regional values. Actual values vary by time of day and season.
3. **GPU-only Accounting**: Does not include CPU, memory, storage, or networking power.
4. **Training Only**: Does not account for model development, experimentation, or inference costs.

For more accurate measurements, consider using runtime power monitoring tools like:
- NVIDIA DCGM (Data Center GPU Manager)
- CodeCarbon
- Cloud provider carbon dashboards

## CSV Output Format

Results are appended to `emissions.csv` with the following columns:

```csv
run_name,timestamp,gpu_model,gpu_count,duration_hours,utilization,region,carbon_intensity_kg_co2_kwh,pue,energy_gpu_kwh,energy_total_kwh,emissions_kg_co2
```

**Example row:**
```csv
resnet50_training,2025-11-13T18:36:37.851337,A100,8,24,0.85,us-east-1,0.448,1.2,65.28,78.336,35.094
```

This format allows for:
- Time-series analysis of training emissions
- Comparison across different models and configurations
- Integration with carbon accounting tools
- Export to spreadsheets and data visualization tools

## Dependencies

- **Python 3.6+**
- **Standard library only** (json, csv, datetime, pathlib, os)

No external packages required!

## License

MIT License - See main repository LICENSE file

## Author

Pascal Joly - IT Climate Ed, LLC

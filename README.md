# The Telehealth Paradox: Texas County Analysis

An interactive data visualization exploring the relationship between healthcare need and telehealth adoption across Texas counties.

## Key Findings

**The Paradox:** Low-income populations actually *use* telehealth at higher rates when they have access, yet counties with the greatest healthcare need face the most barriers to access.

### What the Visualization Shows

1. **County Need Map** - Interactive choropleth of Texas showing a "Telehealth Need Index" (composite of uninsured rate + poverty rate)
2. **Adoption Timeline** - State-level telehealth usage trends (2020-2024) comparing Medicare-only vs dual-eligible (low-income) populations
3. **Top 10 Counties** - Bar chart highlighting counties with highest need
4. **County Search** - Dropdown to search and highlight any Texas county

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install geopandas pandas numpy plotly
```

### 2. Run the Visualization

```bash
python visualization.py
```

This will open three interactive visualizations in your browser:
- Main paradox dashboard (map + charts)
- Need vs income scatter analysis
- Regional patterns breakdown

## Data Sources

- **SAHIE (Small Area Health Insurance Estimates)** - County-level uninsured rates
- **SAIPE (Small Area Income and Poverty Estimates)** - County-level poverty and income data
- **CMS Medicare Telehealth Trends** - State-level telehealth adoption data (2020-2024)
- **Census Bureau Shapefiles** - Texas county geometries

## Project Structure

```
visualization_data/
├── visualization.py              # Main visualization script
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── SAHIE_12-04-2025.csv         # Uninsured rates data
├── saipe_tx_23.txt              # Poverty/income data
├── cb_2018_48_cousub_500k/      # Texas shapefile
└── Medicare Telehealth Trends/   # CMS telehealth data
```

## Features

- **Interactive Maps** - Hover over counties to see detailed statistics
- **County Search** - Dropdown menu to find and highlight any county
- **Responsive Charts** - All visualizations are fully interactive with zoom/pan
- **Dark Theme** - Modern dark aesthetic optimized for presentations

## The Story

This visualization supports a policy argument: **Telehealth infrastructure investment in high-need counties could have outsized impact on healthcare equity.**

The data shows:
- Border regions and rural West Texas have the highest need
- Low-income populations demonstrate higher telehealth adoption rates when given access
- The barrier is *access*, not *interest*

## Authors

Data Science Visualization Project Team

## License

MIT License


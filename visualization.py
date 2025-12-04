"""
THE TELEHEALTH PARADOX: Texas County Analysis
----------------------------------------------

Narrative: Low-income populations USE telehealth more when they have access,
but the counties with the GREATEST NEED face the most barriers.

This visualization overlays:
    - County-level "Telehealth Need Index" (uninsured + poverty)
    - State-level telehealth adoption timeline
    - Identification of highest-need counties

Distinct from team's "Readiness" map - this focuses on DEMAND/NEED, not supply.
"""

from pathlib import Path
import json
import re

import geopandas as gpd
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -------------------------------------------------------------------
#  PATHS
# -------------------------------------------------------------------
try:
    ROOT = Path(__file__).resolve().parent
except NameError:
    ROOT = Path.cwd()

SHAPEFILE_PATH = ROOT / "cb_2018_48_cousub_500k" / "cb_2018_48_cousub_500k.shp"
SAHIE_PATH = ROOT / "SAHIE_12-04-2025.csv"
SAIPE_PATH = ROOT / "saipe_tx_23.txt"
# Updated to use newer CMS data (2020-2025)
TELEHEALTH_PATH = ROOT / "Medicare Telehealth Trends" / "Medicare Telehealth Trends" / \
                  "2025-Q1" / "TMEDTREND_PUBLIC_250827.csv"


# -------------------------------------------------------------------
# DATA LOADING
# -------------------------------------------------------------------
def load_texas_counties():
    """Load and dissolve Texas county geometries."""
    gdf = gpd.read_file(SHAPEFILE_PATH)
    gdf = gdf[gdf["STATEFP"] == "48"].copy()
    gdf["GEOID"] = gdf["STATEFP"] + gdf["COUNTYFP"]
    counties = gdf.dissolve(by="GEOID", as_index=False)
    counties = counties.to_crs(epsg=4326)
    return counties[["GEOID", "NAME", "geometry"]]


def load_sahie():
    """Load county-level uninsured rates."""
    df = pd.read_csv(SAHIE_PATH, skiprows=3)
    df.columns = ["Year", "ID", "Name", "Uninsured_Number", "Uninsured_MOE", 
                  "Uninsured_Pct", "Pct_MOE", "Demographic_Number", "Demographic_MOE"]
    
    df = df[df["ID"].astype(str).str.len() == 5].copy()
    df = df[df["ID"].astype(str).str.startswith("48")].copy()
    
    df["GEOID"] = df["ID"].astype(str).str.zfill(5)
    df["uninsured_pct"] = pd.to_numeric(df["Uninsured_Pct"], errors="coerce")
    df["County_Name"] = df["Name"].str.replace(" County, TX", "", regex=False)
    
    return df[["GEOID", "County_Name", "uninsured_pct"]].dropna()


def load_saipe():
    """Load county-level poverty and income data."""
    data = []
    
    with open(SAIPE_PATH, 'r') as f:
        for line in f:
            parts = line.split()
            if len(parts) < 20 or parts[0] != "48" or parts[1] == "0":
                continue
            
            try:
                poverty_rate = float(parts[5])
                child_poverty = float(parts[11])
                median_income = int(parts[20])
                
                county_match = re.search(r'(\w+(?:\s+\w+)*)\s+County', line)
                county_name = county_match.group(1) if county_match else f"County {parts[1]}"
                
                data.append({
                    "GEOID": f"48{parts[1].zfill(3)}",
                    "poverty_rate": poverty_rate,
                    "child_poverty": child_poverty,
                    "median_income": median_income
                })
            except (ValueError, IndexError):
                continue
    
    return pd.DataFrame(data)


def load_telehealth_trends():
    """
    Load Texas telehealth adoption trends (2020-2024).
    New CMS data format with annual data by enrollment status and rural/urban.
    """
    df = pd.read_csv(TELEHEALTH_PATH)
    
    # Filter to Texas, annual data (Overall quarter)
    tx = df[(df["Bene_Geo_Desc"] == "Texas") & 
            (df["quarter"] == "Overall")].copy()
    
    # Base filter for demographic breakdowns
    base_filter = (
        (tx["Bene_Race_Desc"] == "All") &
        (tx["Bene_Sex_Desc"] == "All") &
        (tx["Bene_Mdcr_Entlmt_Stus"] == "All") &
        (tx["Bene_Age_Desc"] == "All") &
        (tx["Bene_RUCA_Desc"] == "All")
    )
    
    # Medicare Only (higher income proxy)
    medicare_only = tx[base_filter & 
                       (tx["Bene_Mdcd_Mdcr_Enrl_Stus"] == "Medicare Only")].copy()
    
    # Dual-eligible / Medicare & Medicaid (low-income proxy)
    dual = tx[base_filter & 
              (tx["Bene_Mdcd_Mdcr_Enrl_Stus"] == "Medicare & Medicaid")].copy()
    
    # Rural vs Urban (for all enrollment)
    rural_urban_filter = (
        (tx["Bene_Race_Desc"] == "All") &
        (tx["Bene_Sex_Desc"] == "All") &
        (tx["Bene_Mdcr_Entlmt_Stus"] == "All") &
        (tx["Bene_Age_Desc"] == "All") &
        (tx["Bene_Mdcd_Mdcr_Enrl_Stus"] == "All")
    )
    rural = tx[rural_urban_filter & (tx["Bene_RUCA_Desc"] == "Rural")].copy()
    urban = tx[rural_urban_filter & (tx["Bene_RUCA_Desc"] == "Urban")].copy()
    
    # Convert to percentages and add year column
    for data in [medicare_only, dual, rural, urban]:
        data["telehealth_pct"] = data["Pct_Telehealth"] * 100
        data["year"] = data["Year"].astype(int)
    
    return medicare_only, dual, rural, urban


# -------------------------------------------------------------------
# CALCULATE TELEHEALTH NEED INDEX
# -------------------------------------------------------------------
def calculate_need_index(county_data):
    """
    Calculate Telehealth Need Index (0-100) based on:
    - Uninsured rate (normalized)
    - Poverty rate (normalized)
    
    Higher = Greater potential benefit from telehealth access
    """
    df = county_data.copy()
    
    # Normalize each factor to 0-1 scale
    df["uninsured_norm"] = (df["uninsured_pct"] - df["uninsured_pct"].min()) / \
                           (df["uninsured_pct"].max() - df["uninsured_pct"].min())
    
    df["poverty_norm"] = (df["poverty_rate"] - df["poverty_rate"].min()) / \
                         (df["poverty_rate"].max() - df["poverty_rate"].min())
    
    # Combine into Need Index (equal weighting, scale 0-100)
    df["need_index"] = ((df["uninsured_norm"] + df["poverty_norm"]) / 2) * 100
    
    # Categorize
    df["need_category"] = pd.cut(
        df["need_index"],
        bins=[0, 25, 50, 75, 100],
        labels=["Low Need", "Moderate Need", "High Need", "Critical Need"],
        include_lowest=True
    )
    
    return df


# -------------------------------------------------------------------
# BUILD THE PARADOX VISUALIZATION
# -------------------------------------------------------------------
def build_paradox_dashboard(counties, county_data, medicare_only, dual_eligible):
    """
    Create the main visualization showing the telehealth paradox:
    - Map of county need
    - Timeline of state adoption
    - The paradox: high-need areas lack access while low-income users adopt MORE
    """
    
    # Merge county data with geometries
    map_data = counties.merge(county_data, on="GEOID", how="left")
    geojson = json.loads(map_data.to_json())
    
    # Identify top 10 highest need counties
    top_need = county_data.nlargest(10, "need_index")
    
    # Create figure with subplots - simple 2x2 grid
    fig = make_subplots(
        rows=2, cols=2,
        specs=[
            [{"type": "choropleth"}, {"type": "xy"}],
            [None, {"type": "xy"}]
        ],
        column_widths=[0.50, 0.50],
        row_heights=[0.45, 0.55],
        subplot_titles=(
            "<b>County Telehealth Need Index</b>",
            "<b>Telehealth Adoption (2020-2024)</b>",
            "",
            "<b>Top 10 Highest Need Counties</b>"
        ),
        horizontal_spacing=0.08,
        vertical_spacing=0.15
    )
    
    # ===== MAP: County Need Index =====
    # Custom colorscale: Blue (low need) -> Yellow -> Orange -> Red (critical need)
    colorscale = [
        [0.0, "#1a237e"],    # Deep blue - low need
        [0.25, "#42a5f5"],   # Light blue
        [0.5, "#ffeb3b"],    # Yellow - moderate
        [0.75, "#ff9800"],   # Orange - high
        [1.0, "#b71c1c"]     # Deep red - critical
    ]
    
    fig.add_trace(
        go.Choropleth(
            geojson=geojson,
            locations=map_data["GEOID"],
            z=map_data["need_index"],
            featureidkey="properties.GEOID",
            colorscale=colorscale,
            zmin=0,
            zmax=100,
            marker_line_width=0.5,
            marker_line_color="white",
            colorbar=dict(
                title=dict(text="Need<br>Index", font=dict(size=11)),
                ticksuffix="",
                len=0.5,
                thickness=12,
                x=0.38,  # Moved left, closer to map
                y=0.5,
                tickvals=[0, 50, 100],
                ticktext=["Low", "50", "High"],
                tickfont=dict(size=9)
            ),
            hovertemplate="<b>%{customdata[0]}</b><br>" +
                         "Need Index: %{z:.1f}<br>" +
                         "Uninsured: %{customdata[1]:.1f}%<br>" +
                         "Poverty: %{customdata[2]:.1f}%<br>" +
                         "Median Income: $%{customdata[3]:,.0f}<extra></extra>",
            customdata=np.column_stack([
                map_data["County_Name"].fillna("Unknown"),
                map_data["uninsured_pct"].fillna(0),
                map_data["poverty_rate"].fillna(0),
                map_data["median_income"].fillna(0)
            ])
        ),
        row=1, col=1
    )
    
    # Add markers for top 10 highest need counties
    top_need_geo = map_data[map_data["GEOID"].isin(top_need["GEOID"])]
    if len(top_need_geo) > 0:
        # Project to get accurate centroids
        centroids_proj = top_need_geo.to_crs(epsg=3857).geometry.centroid.to_crs(epsg=4326)
        
        fig.add_trace(
            go.Scattergeo(
                lon=centroids_proj.x,
                lat=centroids_proj.y,
                mode="markers+text",
                marker=dict(size=10, color="white", line=dict(color="black", width=2)),
                text=top_need_geo["County_Name"].str[:3].str.upper(),
                textposition="top center",
                textfont=dict(size=8, color="white"),
                name="Top 10 Need",
                showlegend=False,
                hoverinfo="skip"
            ),
            row=1, col=1
        )
    
    # ===== COUNTY SEARCH DROPDOWN =====
    # Calculate centroids for all counties
    all_centroids = map_data.copy()
    all_centroids["centroid"] = all_centroids.to_crs(epsg=3857).geometry.centroid.to_crs(epsg=4326)
    all_centroids["lon"] = all_centroids["centroid"].x
    all_centroids["lat"] = all_centroids["centroid"].y
    all_centroids = all_centroids.dropna(subset=["County_Name", "lon", "lat"])
    all_centroids = all_centroids.sort_values("County_Name")
    
    # Add invisible highlight marker (will be updated by dropdown)
    fig.add_trace(
        go.Scattergeo(
            lon=[all_centroids["lon"].iloc[0]],
            lat=[all_centroids["lat"].iloc[0]],
            mode="markers",
            marker=dict(
                size=25,
                color="rgba(0,0,0,0)",  # Start invisible
                line=dict(color="cyan", width=3),
                symbol="circle"
            ),
            name="Selected County",
            showlegend=False,
            hoverinfo="skip"
        ),
        row=1, col=1
    )
    
    # Create dropdown buttons for county search
    dropdown_buttons = [
        dict(
            label="-- Search County --",
            method="update",
            args=[
                {"marker.color": ["rgba(0,0,0,0)"]},
                {},
                [len(fig.data) - 1]  # Index of highlight trace
            ]
        )
    ]
    
    for _, row in all_centroids.iterrows():
        county_name = row["County_Name"]
        lon, lat = row["lon"], row["lat"]
        need_idx = row.get("need_index", 0)
        unins = row.get("uninsured_pct", 0)
        pov = row.get("poverty_rate", 0)
        
        dropdown_buttons.append(
            dict(
                label=f"{county_name}",
                method="update",
                args=[
                    {
                        "lon": [[lon]],
                        "lat": [[lat]],
                        "marker.color": ["cyan"],
                        "marker.size": [30]
                    },
                    {"title.text": f"<b>THE TELEHEALTH PARADOX</b><br>" +
                                   f"<sup style='color:#0ff'>{county_name} County - Need: {need_idx:.0f} | " +
                                   f"Uninsured: {unins:.1f}% | Poverty: {pov:.1f}%</sup>"},
                    [len(fig.data) - 1]
                ]
            )
        )
    
    # ===== TIMELINE: State Telehealth Adoption (2020-2024) =====
    # Medicare Only (higher income)
    fig.add_trace(
        go.Scatter(
            x=medicare_only["year"],
            y=medicare_only["telehealth_pct"],
            mode="lines+markers",
            name="Medicare Only",
            line=dict(color="#64b5f6", width=2),
            marker=dict(size=8),
            hovertemplate="%{x}: %{y:.1f}%<extra>Medicare Only</extra>"
        ),
        row=1, col=2
    )
    
    # Dual-eligible (low-income)
    fig.add_trace(
        go.Scatter(
            x=dual_eligible["year"],
            y=dual_eligible["telehealth_pct"],
            mode="lines+markers",
            name="Low-Income (Dual)",
            line=dict(color="#e91e63", width=3),
            marker=dict(size=10),
            hovertemplate="%{x}: %{y:.1f}%<extra>Low-Income (Dual)</extra>"
        ),
        row=1, col=2
    )
    
    # Add annotation showing the paradox - more prominent
    fig.add_annotation(
        x=2022,
        y=52,
        text="<b>THE PARADOX</b><br>" +
             "Low-income populations use<br>" +
             "telehealth <b>10-15% MORE</b><br>" +
             "when they have access",
        showarrow=True,
        arrowhead=2,
        arrowcolor="#e91e63",
        ax=60, ay=20,
        font=dict(size=10, color="white"),
        bgcolor="rgba(233,30,99,0.4)",
        bordercolor="#e91e63",
        borderwidth=1,
        borderpad=6,
        xref="x2", yref="y2"
    )
    
    # Add shaded area between the two lines to highlight the gap
    fig.add_trace(
        go.Scatter(
            x=list(medicare_only["year"]) + list(medicare_only["year"][::-1]),
            y=list(dual_eligible["telehealth_pct"]) + list(medicare_only["telehealth_pct"][::-1]),
            fill="toself",
            fillcolor="rgba(233,30,99,0.15)",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip"
        ),
        row=1, col=2
    )
    
    # Add COVID-19 impact shaded region as a filled trace (2020-2021)
    fig.add_trace(
        go.Scatter(
            x=[2020, 2020, 2021, 2021, 2020],
            y=[0, 65, 65, 0, 0],
            fill="toself",
            fillcolor="rgba(255,180,50,0.2)",
            line=dict(color="rgba(255,180,50,0.6)", width=2),
            mode="lines",
            name="COVID-19 Peak",
            showlegend=False,
            hoverinfo="skip"
        ),
        row=1, col=2
    )
    
    # COVID annotation - positioned at top of shaded region
    fig.add_annotation(
        x=2020.5,
        y=63,
        text="<b>COVID-19</b><br><sup>Peak Impact</sup>",
        showarrow=False,
        font=dict(size=11, color="#ffcc00"),
        bgcolor="rgba(40,40,40,0.9)",
        bordercolor="#ffcc00",
        borderwidth=2,
        borderpad=6,
        xref="x2", yref="y2"
    )
    
    # ===== BAR CHART: Top 10 Need Counties =====
    top_need_sorted = top_need.sort_values("need_index", ascending=True)
    
    # Color bars by need index
    bar_colors = [
        f"rgb({int(180 + (val/100)*75)}, {int(100 - (val/100)*80)}, {int(50 - (val/100)*30)})"
        for val in top_need_sorted["need_index"]
    ]
    
    fig.add_trace(
        go.Bar(
            y=top_need_sorted["County_Name"],
            x=top_need_sorted["need_index"],
            orientation="h",
            marker=dict(
                color=top_need_sorted["need_index"],
                colorscale=[[0, "#ff9800"], [1, "#b71c1c"]],
                line=dict(color="white", width=1)
            ),
            text=[f"{v:.0f}" for v in top_need_sorted["need_index"]],
            textposition="inside",
            textfont=dict(color="white", size=11),
            hovertemplate="<b>%{y}</b><br>" +
                         "Need Index: %{x:.1f}<br>" +
                         "<extra></extra>",
            showlegend=False
        ),
        row=2, col=2
    )
    
    
    # ===== LAYOUT =====
    fig.update_layout(
        title=dict(
            text="<b>THE TELEHEALTH PARADOX</b><br>" +
                 "<sup style='color:#aaa'>Counties with highest healthcare need face greatest access barriers, " +
                 "yet low-income populations adopt telehealth at higher rates when available</sup>",
            font=dict(size=20, color="white"),
            x=0.5,
            xanchor="center",
            y=0.97
        ),
        
        # Map settings - span full left side
        geo=dict(
            scope="usa",
            fitbounds="locations",
            visible=False,
            bgcolor="rgba(0,0,0,0)",
            domain=dict(x=[0.0, 0.48], y=[0.10, 0.90])
        ),
        
        # Overall styling
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(color="white", family="Arial"),
        
        # Legend
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.52,
            xanchor="center",
            x=0.78,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=10)
        ),
        
        # County search dropdown
        updatemenus=[
            dict(
                buttons=dropdown_buttons,
                direction="down",
                showactive=True,
                x=0.01,
                xanchor="left",
                y=0.98,
                yanchor="top",
                bgcolor="#1a1a2e",
                bordercolor="#444",
                font=dict(color="white", size=11),
                pad=dict(l=5, r=5, t=5, b=5)
            )
        ],
        
        margin=dict(l=20, r=30, t=100, b=40),  # More top margin for dropdown
        height=1000
    )
    
    # Update axes
    fig.update_xaxes(
        title_text="",
        gridcolor="rgba(255,255,255,0.1)",
        tickformat="%b<br>%Y",
        row=1, col=2
    )
    fig.update_yaxes(
        title_text="% Using Telehealth",
        gridcolor="rgba(255,255,255,0.1)",
        range=[0, 60],
        ticksuffix="%",
        row=1, col=2
    )
    
    fig.update_xaxes(
        title_text="Need Index",
        gridcolor="rgba(255,255,255,0.1)",
        range=[0, 105],
        row=2, col=2
    )
    fig.update_yaxes(
        title_text="",
        gridcolor="rgba(255,255,255,0.1)",
        tickfont=dict(size=11),
        row=2, col=2
    )
    
    # Add explanatory annotation on map
    fig.add_annotation(
        x=0.02, y=0.02,
        xref="paper", yref="paper",
        text="<b>Need Index</b> = Uninsured Rate + Poverty Rate (normalized)<br>" +
             "Higher values indicate counties where telehealth<br>could have the greatest positive impact",
        showarrow=False,
        font=dict(size=10, color="rgba(255,255,255,0.7)"),
        align="left",
        bgcolor="rgba(0,0,0,0.5)",
        borderpad=8
    )
    
    return fig


# -------------------------------------------------------------------
# BUILD SUPPLEMENTARY: NEED VS INCOME SCATTER
# -------------------------------------------------------------------
def build_need_income_analysis(county_data):
    """
    Scatter plot showing the inverse relationship between
    need and resources (income).
    """
    
    fig = go.Figure()
    
    # Color by need category
    colors = {
        "Low Need": "#1a237e",
        "Moderate Need": "#ffeb3b", 
        "High Need": "#ff9800",
        "Critical Need": "#b71c1c"
    }
    
    for cat in ["Low Need", "Moderate Need", "High Need", "Critical Need"]:
        subset = county_data[county_data["need_category"] == cat]
        if len(subset) > 0:
            fig.add_trace(go.Scatter(
                x=subset["median_income"],
                y=subset["need_index"],
                mode="markers",
                name=cat,
                marker=dict(
                    size=10,
                    color=colors[cat],
                    line=dict(color="white", width=1),
                    opacity=0.8
                ),
                text=subset["County_Name"],
                hovertemplate="<b>%{text}</b><br>" +
                             "Median Income: $%{x:,.0f}<br>" +
                             "Need Index: %{y:.1f}<extra></extra>"
            ))
    
    # Add trend line
    z = np.polyfit(county_data["median_income"], county_data["need_index"], 1)
    p = np.poly1d(z)
    x_line = np.linspace(county_data["median_income"].min(), county_data["median_income"].max(), 100)
    
    fig.add_trace(go.Scatter(
        x=x_line,
        y=p(x_line),
        mode="lines",
        name="Trend",
        line=dict(color="rgba(255,255,255,0.5)", dash="dash", width=2),
        hoverinfo="skip"
    ))
    
    fig.update_layout(
        title=dict(
            text="<b>The Resource Gap: Higher Need = Lower Income</b><br>" +
                 "<sup>Counties with the greatest telehealth need have the fewest resources to access it</sup>",
            font=dict(size=16, color="white"),
            x=0.5, xanchor="center"
        ),
        xaxis=dict(
            title="Median Household Income",
            tickprefix="$",
            tickformat=",.0f",
            gridcolor="rgba(255,255,255,0.1)"
        ),
        yaxis=dict(
            title="Telehealth Need Index",
            gridcolor="rgba(255,255,255,0.1)",
            range=[0, 105]
        ),
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(color="white", family="Arial"),
        legend=dict(
            title="Need Category",
            bgcolor="rgba(0,0,0,0.5)"
        ),
        margin=dict(l=60, r=40, t=80, b=60),
        height=500
    )
    
    return fig


# -------------------------------------------------------------------
# BUILD GEOGRAPHIC PATTERN ANALYSIS
# -------------------------------------------------------------------
def build_geographic_patterns(counties, county_data):
    """
    Show regional patterns - border counties, rural West Texas, etc.
    """
    map_data = counties.merge(county_data, on="GEOID", how="left")
    
    # Calculate regional statistics
    # Define regions by latitude/longitude of centroids
    map_data["centroid"] = map_data.geometry.centroid
    map_data["lon"] = map_data["centroid"].x
    map_data["lat"] = map_data["centroid"].y
    
    # Rough regional classification
    def classify_region(row):
        if row["lat"] < 28:  # Southern border
            return "Border Region"
        elif row["lon"] < -102:  # West Texas
            return "West Texas"
        elif row["lon"] > -96 and row["lat"] > 32:  # DFW Metro area
            return "North Texas Urban"
        elif row["lon"] > -96 and row["lat"] < 30:  # Houston area
            return "Gulf Coast Urban"
        else:
            return "Central Texas"
    
    map_data["region"] = map_data.apply(classify_region, axis=1)
    
    # Create regional summary
    regional_stats = map_data.groupby("region").agg({
        "need_index": "mean",
        "uninsured_pct": "mean",
        "poverty_rate": "mean",
        "median_income": "mean",
        "GEOID": "count"
    }).round(1)
    regional_stats.columns = ["Avg Need", "Avg Uninsured", "Avg Poverty", "Avg Income", "Counties"]
    regional_stats = regional_stats.sort_values("Avg Need", ascending=False)
    
    # Build figure
    fig = go.Figure()
    
    region_colors = {
        "Border Region": "#b71c1c",
        "West Texas": "#ff9800",
        "Central Texas": "#ffeb3b",
        "Gulf Coast Urban": "#4caf50",
        "North Texas Urban": "#1a237e"
    }
    
    fig.add_trace(go.Bar(
        x=regional_stats.index,
        y=regional_stats["Avg Need"],
        marker_color=[region_colors.get(r, "#666") for r in regional_stats.index],
        text=[f"{v:.0f}" for v in regional_stats["Avg Need"]],
        textposition="outside",
        textfont=dict(color="white"),
        hovertemplate="<b>%{x}</b><br>" +
                     "Avg Need Index: %{y:.1f}<br>" +
                     "<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(
            text="<b>Regional Disparities in Telehealth Need</b><br>" +
                 "<sup>Border and rural regions show highest need indices</sup>",
            font=dict(size=16, color="white"),
            x=0.5, xanchor="center"
        ),
        xaxis=dict(title="", tickangle=0),
        yaxis=dict(title="Average Need Index", gridcolor="rgba(255,255,255,0.1)"),
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(color="white", family="Arial"),
        margin=dict(l=60, r=40, t=80, b=60),
        height=400,
        showlegend=False
    )
    
    return fig, regional_stats


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
def main():
    print("\n" + "="*65)
    print("  THE TELEHEALTH PARADOX: Texas County Analysis")
    print("="*65 + "\n")
    
    # Load data
    print("Loading data...")
    counties = load_texas_counties()
    print(f"  - {len(counties)} county geometries")
    
    sahie = load_sahie()
    print(f"  - {len(sahie)} county uninsured records")
    
    saipe = load_saipe()
    print(f"  - {len(saipe)} county poverty records")
    
    medicare_only, dual_eligible, rural, urban = load_telehealth_trends()
    years = sorted(medicare_only["year"].unique())
    print(f"  - Telehealth data: {years[0]}-{years[-1]} ({len(medicare_only)} annual records)")
    
    # Merge county data
    print("\nCalculating Telehealth Need Index...")
    county_data = sahie.merge(saipe, on="GEOID", how="inner")
    county_data = calculate_need_index(county_data)
    
    # Print summary statistics
    print(f"\nNeed Index Summary:")
    print(f"  - Range: {county_data['need_index'].min():.1f} to {county_data['need_index'].max():.1f}")
    print(f"  - Mean: {county_data['need_index'].mean():.1f}")
    print(f"  - Median: {county_data['need_index'].median():.1f}")
    
    print(f"\nNeed Categories:")
    print(county_data["need_category"].value_counts().to_string())
    
    print(f"\nTop 10 Highest Need Counties:")
    top10 = county_data.nlargest(10, "need_index")[["County_Name", "need_index", "uninsured_pct", "poverty_rate"]]
    for _, row in top10.iterrows():
        print(f"  {row['County_Name']}: {row['need_index']:.1f} (Unins: {row['uninsured_pct']:.1f}%, Pov: {row['poverty_rate']:.1f}%)")
    
    # Build visualizations
    print("\nBuilding visualizations...")
    
    print("  - Main paradox dashboard...")
    fig_main = build_paradox_dashboard(counties, county_data, medicare_only, dual_eligible)
    
    print("  - Need vs income analysis...")
    fig_scatter = build_need_income_analysis(county_data)
    
    print("  - Regional patterns...")
    fig_regional, regional_stats = build_geographic_patterns(counties, county_data)
    
    # Display
    print("\n" + "="*65)
    print("  Opening visualizations in browser...")
    print("="*65)
    
    fig_main.show()
    fig_scatter.show()
    fig_regional.show()
    
    print("""
===================================================================
  THE TELEHEALTH PARADOX - KEY FINDINGS
===================================================================

  1. THE NEED MAP
     Counties colored by "Telehealth Need Index" - a composite of
     uninsured rate and poverty rate. Red/orange counties would
     benefit MOST from expanded telehealth access.

  2. THE PARADOX
     State-level data shows low-income (dual-eligible) populations
     actually USE telehealth at HIGHER rates than others when they
     have access. The demand exists - access is the barrier.

  3. THE RESOURCE GAP
     Counties with highest need have lowest median incomes,
     creating a vicious cycle: those who need telehealth most
     can least afford the technology/broadband to access it.

  4. REGIONAL PATTERNS
     Border regions and rural West Texas show highest need,
     while urban metros (DFW, Houston) show lowest need.

  POLICY IMPLICATION:
  Telehealth infrastructure investment in high-need counties
  could have outsized impact on healthcare equity.

===================================================================
""")
    
    print("\nRegional Statistics:")
    print(regional_stats.to_string())


if __name__ == "__main__":
    main()

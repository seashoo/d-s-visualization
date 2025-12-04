# Speaker Notes: The Telehealth Paradox
## Texas County Analysis - Data Visualization Presentation

---

## OPENING (30 seconds)

> "Our visualization explores what we call **The Telehealth Paradox** - a counterintuitive finding that challenges assumptions about healthcare technology adoption. We found that the populations who would benefit MOST from telehealth are often the ones with the LEAST access to it - but when they DO have access, they use it at significantly higher rates than wealthier populations."

---

## PART 1: DATA SOURCES & METHODOLOGY

### Source 1: SAHIE (Small Area Health Insurance Estimates)
**File:** `SAHIE_12-04-2025.csv`
**Publisher:** U.S. Census Bureau

**Why This Source:**
- SAHIE is the **gold standard** for county-level health insurance data
- Provides model-based estimates that fill gaps where survey data is sparse
- Updated annually with consistent methodology across all U.S. counties
- Specifically designed for small-area (county-level) analysis

**What We Extract:**
- County-level **uninsured rates** (percentage of population without health insurance)
- This is critical because uninsured populations have the greatest potential to benefit from telehealth as an affordable care alternative

**Data Quality Notes:**
- Margins of error are provided but we use point estimates for visualization clarity
- 2023 data represents pre-pandemic baseline conditions normalizing

---

### Source 2: SAIPE (Small Area Income and Poverty Estimates)
**File:** `saipe_tx_23.txt`
**Publisher:** U.S. Census Bureau

**Why This Source:**
- Official Census Bureau estimates used for federal fund allocation
- County-level granularity essential for geographic analysis
- Provides both poverty rates AND median income - allowing us to see the full economic picture

**What We Extract:**
- **Poverty rate** (% of population below federal poverty line)
- **Median household income** (economic capacity indicator)

**Why Poverty Matters for Telehealth:**
- Poverty correlates with healthcare access barriers
- Low-income individuals often lack transportation to in-person appointments
- Telehealth could theoretically solve access issues - but requires technology/broadband

---

### Source 3: CMS Medicare Telehealth Trends
**File:** `TMEDTREND_PUBLIC_250827.csv`
**Publisher:** Centers for Medicare & Medicaid Services (CMS)

**Why This Source:**
- CMS is the **only reliable source** for actual telehealth utilization data
- Covers Medicare population (65+ and disabled) - a key telehealth demographic
- Crucially provides breakdown by **enrollment status**:
  - **Medicare Only** = Higher income proxy (have private coverage or can afford out-of-pocket)
  - **Medicare & Medicaid (Dual-Eligible)** = Low-income proxy (qualify for Medicaid based on income)

**Why This Distinction Matters:**
- Dual-eligible beneficiaries are among the poorest Americans
- If they use telehealth MORE than wealthier counterparts, it proves **demand exists**
- The barrier is ACCESS, not INTEREST or willingness

**Limitations Acknowledged:**
- This is STATE-level data, not county-level
- We cannot directly show telehealth usage by county
- We use it to establish the PARADOX, then apply county-level need indices

---

### Source 4: Census Bureau TIGER/Line Shapefiles
**File:** `cb_2018_48_cousub_500k/`
**Publisher:** U.S. Census Bureau

**Why This Source:**
- Official geographic boundaries for Texas counties
- High-resolution (500k scale) appropriate for state-level visualization
- Standardized GEOID codes enable clean data joins

**Technical Note:**
- Original file contains county subdivisions - we dissolve by GEOID to get county-level polygons
- Projection converted to WGS84 (EPSG:4326) for web mapping compatibility

---

## PART 2: THE TELEHEALTH NEED INDEX - METHODOLOGY

### Formula:
```
Need Index = (Normalized Uninsured Rate + Normalized Poverty Rate) / 2 × 100
```

### Normalization Process:
1. **Min-Max Scaling** applied to both metrics independently
2. For Uninsured Rate: `(county_rate - min_rate) / (max_rate - min_rate)`
3. For Poverty Rate: `(county_rate - min_rate) / (max_rate - min_rate)`
4. Average of both normalized values × 100 = Need Index (0-100 scale)

### Why This Approach:
- **Equal weighting** treats both factors as equally important indicators of need
- **Normalization** prevents one metric from dominating due to scale differences
- **0-100 scale** provides intuitive interpretation (higher = more need)

### Category Thresholds:
| Category | Need Index Range | Counties |
|----------|-----------------|----------|
| Critical Need | 70+ | 5 |
| High Need | 55-70 | 76 |
| Moderate Need | 40-55 | 147 |
| Low Need | <40 | 26 |

### Why NOT Include Broadband Data:
- We initially explored FCC broadband data
- **Problem:** FCC data only provides state-level or census tract summaries
- County-level broadband coverage data doesn't exist reliably
- Rather than use unreliable proxies, we focused on NEED (which we CAN measure) and let the PARADOX data speak to ACCESS

---

## PART 3: HOW THIS FITS THE TEAM NARRATIVE

### What Our Teammates Covered:
*(Based on their existing visualizations)*

1. **Telehealth Readiness Map** - Focused on SUPPLY side (infrastructure, provider availability)
2. **Insurance Coverage Trends** - Longitudinal changes in coverage
3. **Broadband Access Analysis** - Technology infrastructure

### What OUR Visualization Adds:

**We focus on DEMAND and NEED - the human side of the equation.**

| Teammate Focus | Our Focus |
|----------------|-----------|
| "Where CAN telehealth work?" | "Where SHOULD it work?" |
| Infrastructure readiness | Population need |
| Provider supply | Patient demand |
| Technology availability | Healthcare gaps |

### The Key Distinction:
- Teammates show WHERE telehealth infrastructure exists
- WE show WHERE it would have the GREATEST IMPACT
- Together, we can identify the **GAP**: high-need areas with low readiness

### Policy Implication:
> "If we overlay our NEED map with the team's READINESS map, the mismatch becomes clear: the counties colored red on OUR map (highest need) are often the same ones colored poorly on the readiness map. This isn't coincidence - it's systemic inequity."

---

## PART 4: VISUALIZATION-BY-VISUALIZATION BREAKDOWN

### Visualization 1: The Main Dashboard

#### Component A: County Need Map (Choropleth)
**What It Shows:**
- All 254 Texas counties colored by Telehealth Need Index
- Blue = Low need, Yellow = Moderate, Orange = High, Red = Critical

**Key Talking Points:**
- "Notice the concentration of red/orange along the Texas-Mexico border"
- "Hudspeth County (El Paso area) has the highest need index at 85.8"
- "Gulf Coast urban areas (Houston, Galveston) show lowest need - blue"
- "The pattern isn't random - it follows historical healthcare investment patterns"

**Interactive Elements:**
- Hover reveals: County name, Need Index, Uninsured %, Poverty %, Median Income
- Search dropdown to find specific counties
- Top 10 highest need counties marked with white circles

#### Component B: Telehealth Adoption Timeline (2020-2024)
**What It Shows:**
- Two lines: Medicare Only (blue) vs. Low-Income/Dual-Eligible (pink)
- Shaded region between them = The Paradox Gap
- COVID-19 impact highlighted (2020-2021)

**Key Talking Points:**
- "In 2020, 60% of low-income Medicare beneficiaries used telehealth vs 49% of higher-income"
- "That's an **11 percentage point gap** - low-income used MORE"
- "Even as usage declined post-COVID, the gap PERSISTED"
- "By 2024: 35% low-income vs 25% higher-income - still 10 points higher"

**The COVID Context:**
- "The 2020-2021 surge was pandemic-driven - people HAD to use telehealth"
- "But the key insight is WHO used it most when given the opportunity"
- "Low-income populations didn't avoid telehealth - they EMBRACED it"

#### Component C: Top 10 Highest Need Counties (Bar Chart)
**What It Shows:**
- Horizontal bars ranking counties by Need Index
- Color gradient reinforces severity

**Key Talking Points:**
- "These 10 counties should be PRIORITY targets for telehealth investment"
- "8 of 10 are border counties - this is a border health equity issue"
- "Hudspeth (85.8), Zapata (83.6), Hidalgo (79.8) lead the list"
- "Combined population of ~1.2 million Texans in critical need"

---

### Visualization 2: The Resource Gap (Scatter Plot)

**What It Shows:**
- X-axis: Median Household Income
- Y-axis: Telehealth Need Index
- Each dot = one Texas county
- Color = Need Category
- Trendline shows correlation

**The Story:**
> "This chart visualizes the **vicious cycle** of healthcare inequity."

**Key Talking Points:**
- "Clear negative correlation: as income rises, need falls"
- "The red dots (Critical Need) cluster in the $35,000-$50,000 income range"
- "Blue dots (Low Need) are mostly above $90,000 median income"
- "Counties that NEED telehealth most can LEAST AFFORD the technology to access it"

**Statistical Note:**
- The trendline is a simple linear regression showing the relationship
- R² value indicates strength of correlation (you can mention if asked)

---

### Visualization 3: Regional Disparities (Bar Chart)

**What It Shows:**
- Average Need Index by Texas region
- Color-coded by severity

**Regional Definitions:**
| Region | Definition | Counties |
|--------|------------|----------|
| Border Region | Counties along Mexico border | 13 |
| West Texas | Rural west (excluding border) | 30 |
| North Texas Urban | DFW metro area | 21 |
| Central Texas | Austin, San Antonio, rural central | 184 |
| Gulf Coast Urban | Houston, Galveston metro | 6 |

**Key Talking Points:**
- "Border Region averages 67 - nearly DOUBLE the Gulf Coast Urban (34)"
- "This isn't about rural vs. urban - West Texas (48) is similar to Central Texas (42)"
- "The border region is UNIQUELY disadvantaged"
- "Historical underinvestment in border healthcare infrastructure shows here"

---

## PART 5: THE PARADOX EXPLAINED

### What IS The Telehealth Paradox?

**Definition:**
> Low-income populations demonstrate HIGHER telehealth adoption rates when given access, yet they live in areas with the LOWEST access to telehealth infrastructure.

### Why Does This Matter?

1. **Challenges Assumptions:** 
   - Common assumption: "Poor people won't use technology"
   - Reality: They use it MORE when available

2. **Identifies Real Barrier:**
   - The problem isn't DEMAND (people want it)
   - The problem is ACCESS (infrastructure, broadband, devices)

3. **Clarifies Policy Priority:**
   - Don't focus on "convincing" people to use telehealth
   - Focus on ENABLING access in high-need areas

### The Logic Chain:
```
High poverty + High uninsured = High NEED for affordable healthcare
                ↓
When telehealth IS available, low-income USE it more
                ↓
Therefore: DEMAND exists, ACCESS is the barrier
                ↓
Investment in high-need county infrastructure = High ROI for health equity
```

---

## PART 6: LIMITATIONS & HONEST ACKNOWLEDGMENTS

### What We CAN'T Show:
1. **County-level telehealth usage** - This data doesn't exist publicly
2. **Broadband availability by county** - Reliable data not available
3. **Causation** - We show correlation, not proof of causation

### Assumptions Made:
1. Dual-eligible status is a valid proxy for low-income
2. Uninsured + poverty rates capture "need" adequately
3. Medicare population trends generalize to broader population

### What This Means:
> "Our visualization shows WHERE investment should be prioritized and WHY demand exists. It doesn't prove that investment will work - but it provides the evidence-based targeting that policy requires."

---

## CLOSING STATEMENT (30 seconds)

> "The Telehealth Paradox reveals an uncomfortable truth: the same systemic factors that create healthcare need - poverty, lack of insurance, geographic isolation - also create barriers to the solutions that could help. But there's hope in the data: when given access, underserved populations DON'T reject telehealth - they embrace it at higher rates than anyone else. The demand is there. The need is mapped. What's missing is the investment to bridge the gap."

---

## Q&A PREPARATION

### Likely Questions:

**Q: Why did you use Medicare data instead of all-population data?**
> "Medicare is the only source that provides telehealth utilization broken down by income proxy (dual-eligible status). Private insurance data isn't publicly available at this granularity."

**Q: Isn't the high 2020 usage just because of COVID?**
> "Yes, COVID drove the initial surge - but the KEY finding is the DIFFERENTIAL. Low-income used it 10-15% MORE than higher-income even during the same pandemic. The gap persisted through 2024."

**Q: How do you know broadband is the barrier?**
> "We infer this from the income correlation. The counties with highest need have lowest median incomes - averaging $47,500 vs $86,000 for low-need counties. They lack resources for broadband and devices."

**Q: What would you recommend to policymakers?**
> "Target telehealth infrastructure investment in the top 10-20 highest need counties. The data shows demand exists - provide community health centers with telehealth equipment, subsidize broadband in border regions, and create device lending programs."

---

## TECHNICAL NOTES FOR FOLLOW-UP

- **Code Repository:** https://github.com/seashoo/d-s-visualization
- **Dependencies:** geopandas, pandas, numpy, plotly
- **Run Command:** `python visualization.py`
- **Data Vintage:** SAHIE 2023, SAIPE 2023, CMS 2020-2024, Shapefiles 2018

---

*Speaker Notes prepared for: Sahran Ashoor, Carisma Spears, Lisa Zheng*
*Data Science Visualization Project*


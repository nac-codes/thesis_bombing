# Precision vs. Area Bombing Classification Methodology

This document explains the methodology used to classify bombing raids on a precision-to-area bombing continuum based on raid characteristics extracted from historical data.

## Framework Overview

We developed a three-dimensional framework for classifying bombing raids on a scale from precision bombing (score of 0) to area bombing (score of 10):

1. **Target Designation**: Area bombing targets (from INDUSTRIAL book) vs. precision bombing targets (other categories)
2. **Bombing Weight/Tonnage**: Percentile-based distribution of tonnage across raids
3. **Incendiary Usage**: Custom stepped scoring approach for incendiary percentage

## Data Analysis

### Dataset Summary
- Total raids analyzed: 28,815
- Area bombing targets (INDUSTRIAL book): 5,834 (20.2%)
- Precision bombing targets (other books): 22,981 (79.8%)

### Tonnage Statistics
```
count    28815.000000
mean        60.938887
std        162.921558
min          0.000000
25%          2.000000
50%          7.000000 (median)
75%         55.000000
max       4837.000000
```

### Incendiary Percentage Statistics
```
count    28815.000000
mean         8.864473
std         21.451583
min          0.000000
50%          0.000000 (median)
75%          3.566130
90%         32.258065
95%         58.074676
99%        100.000000
max        100.000000
```

### Incendiary Score Distribution
```
count    28815.000000
mean         1.340394
std          2.505621
min          0.000000
25%          0.000000
50%          0.000000
75%          2.997956
90%          5.000000
95%          6.999987
99%         10.000000
max         10.000000
```

## Scoring Methodology

### 1. Target Designation Score
- Area bombing targets (containing "INDUSTRIAL" in the BOOK field): 1 point
- Precision bombing targets: 0 points
- The INDUSTRIAL category primarily includes city areas, town areas, and unidentified targets, which align with area bombing practices

### 2. Tonnage Score
- Based on percentile ranking of tonnage relative to all raids
- Formula: `tonnage_percentile * 10`
- Higher tonnage = higher score (more likely to be area bombing)

### 3. Incendiary Score
- Custom stepped scoring approach that addresses the highly skewed distribution of incendiary usage
- Raids with 0% incendiaries (72.2% of all raids) are given a score of 0
- Non-zero incendiary percentages are scored on a progressive scale:
  - 0-75th percentile (0-3.57%): Scaled from 0-3 points
  - 75-90th percentile (3.57-32.26%): Scaled from 3-5 points
  - 90-95th percentile (32.26-58.07%): Scaled from 5-7 points
  - 95-99th percentile (58.07-100%): Scaled from 7-9 points
  - Top 1% (100%): 9-10 points
- This approach ensures that:
  1. The large number of raids with 0% incendiaries are appropriately scored
  2. Even small usage of incendiaries is recognized (score > 0)
  3. Heavy incendiary usage is properly emphasized with higher scores

### Combined Area Bombing Score
- Weighted average of the component scores:
  - 40% Target Type score (0-10)
  - 30% Tonnage Score (0-10)
  - 30% Incendiary Score (0-10)
- Result is normalized to range from 0-10, where:
  - 0-2: Very Precise bombing
  - 2-4: Precision bombing
  - 4-6: Mixed strategy
  - 6-8: Area bombing
  - 8-10: Heavy area bombing

## Results

### Distribution of Area Bombing Scores
- Minimum score: 0.0
- Maximum score: 10.0
- Mean score: 2.80
- Median score: 2.4

The distribution of scores shows a concentration in the lower range (0-4), indicating that most raids were classified as precision bombing or mixed strategy, with fewer raids classified as clear area bombing.

### Incendiary Score Distribution
| Score Range | Number of Raids | Percentage |
|-------------|----------------|------------|
| 0           | 20,815         | 72.2%      |
| 0.01-1      | 453            | 1.6%       |
| 1-3         | 343            | 1.2%       |
| 3-5         | 4,319          | 15.0%      |
| 5-7         | 1,444          | 5.0%       |
| 7-9         | 672            | 2.3%       |
| 9-10        | 769            | 2.7%       |

### Findings by Target Type
- Industrial/area targets have significantly higher area bombing scores
- Non-industrial/precision targets show lower area bombing scores

## Example Raids Across the Continuum

| Location | Target | Target Score | Tonnage Score | Incendiary Score | Area Bombing Score |
|----------|--------|-------------|---------------|------------------|-------------------|
| STETTIN | CITY AREA | 1 | 9.98 | 9.50 | 9.9 |
| Eberswalde | Unidentified Target | 1 | 8.26 | 9.15 | 9.2 |
| Rostock | City Area | 1 | 4.69 | 7.83 | 7.6 |
| WORMS | Moreval | 1 | 4.42 | 3.61 | 6.0 |
| RATTEN | POCHLARN BONDS | 1 | 2.70 | 3.61 | 5.5 |
| Tarvisio | Motor Truck Depot | 0 | 9.78 | 3.61 | 3.3 |
| Orleans | PARIS LE BOURGET AIRDROME | 0 | 8.55 | 3.61 | 2.8 |
| Vitry en Artois | Airdrome | 0 | 2.70 | 3.61 | 0.9 |
| Rotterdam | Docks and Harbors | 0 | 0.05 | 3.61 | 0.0 |

## Distribution by Category

| Bombing Category | Count | Percentage |
|------------------|-------|------------|
| Very Precise (0-2) | 10,056 | 34.9% |
| Precise (2-4) | 10,502 | 36.4% |
| Mixed (4-6) | 4,257 | 14.8% |
| Area (6-8) | 2,898 | 10.1% |
| Heavy Area (8-10) | 724 | 2.5% |

## Conclusion

This classification framework provides a nuanced way to position individual bombing raids on a precision-to-area bombing continuum. The methodology incorporates multiple factors that historians consider relevant to the distinction between area and precision bombing, with particular attention to handling the skewed distribution of incendiary usage.

The analysis reveals that approximately 71% of raids were predominantly precision bombing in nature, while only about 13% fall clearly into the area bombing category. This supports the historical understanding that while area bombing was a significant strategy, precision bombing was more frequently attempted, though often with varying degrees of success. 
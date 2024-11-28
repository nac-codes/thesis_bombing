# Strategic Bombing in World War II: A Data-Driven Analysis

A comprehensive analysis of World War II strategic bombing using data from the United States Strategic Bombing Survey (USSBS), combining empirical analysis, computational modeling, and theoretical frameworks.

## Overview

This thesis examines the strategic bombing campaign of World War II through multiple analytical lenses:

- Analysis of digitized USSBS attack data
- Economic network modeling of bombing impacts
- Computational analysis of public discourse
- Theoretical framework incorporating sociological perspectives

A pdf version of the thesis is available [here](thesis.pdf).

A markdown version of the thesis is available [here](combined_thesis.md).

## Data Sources

- 8,134 photographs of original USSBS computer printouts
- Over 10,000 newspaper articles (1941-1946)
- USSBS reports and interrogation transcripts
- Historical economic data from German war economy

## Repository Structure

- `attack_data/` - Processed bombing mission data and analysis
- `scripts/` - Python scripts for data processing and analysis
- `deploy/` - PDF generation and deployment tools
- `corpora/` - Text corpus for computational analysis (not included in repo)

## Requirements

- Python 3.8+
- LaTeX distribution
- Required Python packages listed in `scripts/literature_review/requirements.txt`

## Building the PDF

```bash
./deploy/to_pdf.sh
```

## License

All rights reserved. This material is for academic purposes only.
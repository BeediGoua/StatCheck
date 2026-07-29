# StatCheck France

> An uncertainty-aware statistical claim verification system over official French public data, combining hybrid retrieval, multidimensional data matching, reproducible computation, and automatic exploratory analysis.

## Project Overview

StatCheck France is an automated fact-checking pipeline designed to verify quantitative claims against official public data. Unlike standard generative language models that are prone to hallucinating mathematical operations and ignoring dimensional constraints, StatCheck France relies on a hybrid architecture. It uses Natural Language Processing (NLP) strictly for claim extraction and query formulation, while delegating data retrieval and calculations to deterministic, auditable subsystems.

## Problem Statement

Every day, numerous articles, political speeches, and publications use statistics to support arguments:
- *"Youth unemployment has increased by 20% since 2020."*
- *"The population of Paris has decreased by 10% in ten years."*

Verifying these claims requires more than simply finding a number in an official dataset. It requires strict alignment across multiple dimensions:
1. **Indicator Match:** Does the underlying metric match the claim? (e.g., ILO unemployment vs. registered job seekers).
2. **Population:** Does the claim apply to the correct demographic group?
3. **Geography:** Is the territorial scope accurately defined?
4. **Unit & Operation:** Is the math correct? (e.g., confusing a percentage increase with percentage points).
5. **Contextual Integrity:** Is the statistic technically correct but methodologically misleading? (e.g., base effects, cherry-picked timelines, structural series breaks).

## Methodology & Architecture

The system is built on a modular pipeline designed to prioritize accountability and uncertainty management (abstention) over forced generation.

1. **Claim Extraction & Parsing:** Processing natural language inputs to extract structured variables (indicator, territory, period, demographic, and mathematical operation).
2. **Hybrid Retrieval:** Searching the official data catalog using a combination of lexical (BM25) and dense vector (embedding) retrieval to find the most relevant datasets.
3. **Dimensional Resolution:** Strictly mapping the extracted variables to the hierarchical metadata of the official datasets.
4. **Deterministic Computation:** Recomputing the claim's value using a dedicated statistical engine to ensure reproducibility and prevent AI hallucinations.
5. **Exploratory Data Analysis (EDA):** Contextualizing the data by detecting anomalies, structural breaks, or atypical base years.
6. **Calibrated Verdict:** Outputting a nuanced verdict (e.g., Supported, Approximately Supported, Misleading, Insufficient Context, Abstention) along with a comprehensive evidence trail.

## Data Sources

The pipeline prioritizes official, high-quality public statistics APIs to ensure data integrity:
- **INSEE (National Institute of Statistics and Economic Studies):** Primary source for demographic, employment, and macroeconomic data via the Melodi and BDM APIs.
- *(Future integrations: Eurostat for European comparisons, Data.gouv for dataset discovery).*

## Repository Structure

(To be populated as the project architecture is implemented)

## Setup & Installation

(To be populated as the project infrastructure is implemented)
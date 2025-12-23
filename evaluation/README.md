# SWDE Evaluation System

This directory contains the evaluation system for testing web2json-agent against the SWDE (Structured Web Data Extraction) dataset.

## Overview

The SWDE evaluation system:
1. Runs the web2json agent on SWDE dataset websites
2. Compares extracted JSON against groundtruth
3. Computes precision, recall, and F1 scores
4. Generates detailed reports with visualizations
5. **Updates summary.json continuously with progress and metrics**

## Installation

Install required dependencies:

```bash
pip install matplotlib tqdm
```

## Quick Start

### Simplest way: Use the shell script

```bash
# Full evaluation (all verticals and websites)
./run_test.sh

# Resume from previous run (skip completed websites)
./run_test.sh --resume
```

### Using Python directly

```bash
# Full evaluation
python run_evaluation.py

# Resume from previous run
python run_evaluation.py --resume

# Evaluate specific vertical
python run_evaluation.py --vertical book

# Evaluate specific website
python run_evaluation.py --vertical book --website abebooks
```

### Advanced usage

For full control, use the core evaluation module:

```bash
# Evaluate a single website
python evaluation/run_swde_evaluation.py \
  --dataset-dir evaluationSet \
  --groundtruth-dir evaluationSet/groundtruth \
  --output-dir swde_evaluation_output \
  --vertical book \
  --website abebooks

# Resume mode (skip fully completed websites)
python evaluation/run_swde_evaluation.py \
  --dataset-dir evaluationSet \
  --groundtruth-dir evaluationSet/groundtruth \
  --output-dir swde_evaluation_output \
  --resume

# Skip agent execution (reuse existing outputs)
python evaluation/run_swde_evaluation.py \
  --dataset-dir evaluationSet \
  --groundtruth-dir evaluationSet/groundtruth \
  --output-dir swde_evaluation_output \
  --skip-agent

# Skip evaluation (reuse existing reports)
python evaluation/run_swde_evaluation.py \
  --dataset-dir evaluationSet \
  --groundtruth-dir evaluationSet/groundtruth \
  --output-dir swde_evaluation_output \
  --skip-evaluation

# Force complete re-run (ignore all existing outputs)
python evaluation/run_swde_evaluation.py \
  --dataset-dir evaluationSet \
  --groundtruth-dir evaluationSet/groundtruth \
  --output-dir swde_evaluation_output \
  --force

# Combine options for maximum flexibility
python evaluation/run_swde_evaluation.py \
  --dataset-dir evaluationSet \
  --groundtruth-dir evaluationSet/groundtruth \
  --output-dir swde_evaluation_output \
  --resume --skip-agent
```

**Available options:**
- `--dataset-dir`: Root directory of SWDE dataset
- `--groundtruth-dir`: Directory containing groundtruth files
- `--output-dir`: Root directory for outputs
- `--vertical`: Specific vertical to evaluate (optional)
- `--website`: Specific website to evaluate (requires --vertical)
- `--python`: Python command to use (default: python3)
- `--resume`: Skip fully completed websites
- `--skip-agent`: Skip agent execution if outputs exist
- `--skip-evaluation`: Skip evaluation if reports exist
- `--force`: Force re-run everything (overrides all skip options)

## Output Structure

```
swde_evaluation_output/
├── summary.json                  # ⭐ Global progress and metrics (updated continuously)
├── <vertical>/
│   ├── <website>/
│   │   ├── evaluation/
│   │   │   ├── report.html          # Interactive HTML report
│   │   │   ├── evaluation_charts.png # Visualization charts
│   │   │   ├── results.json         # Detailed results
│   │   │   └── summary.csv          # CSV summary
│   │   ├── result/                  # Agent output JSONs
│   │   ├── parsers/                 # Generated parser code
│   │   └── ...
│   └── _summary/
│       └── summary.json             # Vertical-level summary (legacy)
```

### Global Summary File

The `summary.json` file at the root of the output directory contains:
- **Overall metrics**: Weighted average across all completed websites
- **Per-vertical metrics**: Average metrics for each vertical
- **Per-website metrics**: Detailed results for each website
- **Progress tracking**: Completed vs total websites
- **Timestamps**: When each website was evaluated

Example structure:
```json
{
  "timestamp": "2025-12-23T10:30:00",
  "verticals": {
    "book": {
      "websites": {
        "abebooks": {
          "precision": 0.92,
          "recall": 0.88,
          "f1": 0.90,
          "evaluated_pages": 200,
          "attribute_metrics": {...}
        },
        ...
      },
      "metrics": {
        "precision": 0.90,
        "recall": 0.87,
        "f1": 0.88
      },
      "completed_websites": 5,
      "total_websites": 10
    },
    ...
  },
  "overall": {
    "precision": 0.89,
    "recall": 0.86,
    "f1": 0.87,
    "completed_websites": 25,
    "total_websites": 80
  }
}
```

## Resume Mode & Skip Options

The evaluation system provides flexible control over which steps to skip, allowing you to resume interrupted runs or reuse existing outputs:

### Resume Mode (`--resume`)
Skip websites that have been **fully completed** (both agent execution and evaluation):

```bash
# Resume from previous run
python run_evaluation.py --resume

# Or with shell script
./run_test.sh --resume
```

**When to use:**
- Evaluation was interrupted (Ctrl+C, error, timeout)
- You want to continue from where you left off
- Adding more websites to an existing evaluation run

**How it works:**
- Checks `summary.json` for completed websites
- Verifies that both result files and evaluation reports exist
- Skips websites only if all outputs are present
- Updates global metrics as new websites are completed

### Skip Agent Execution (`--skip-agent`)
Reuse existing agent outputs and only re-run evaluation:

```bash
python evaluation/run_swde_evaluation.py \
  --dataset-dir evaluationSet \
  --groundtruth-dir evaluationSet/groundtruth \
  --output-dir swde_evaluation_output \
  --skip-agent
```

**When to use:**
- Agent outputs already exist (from a previous run)
- You want to re-evaluate with different metrics
- Testing evaluation code changes without re-running the agent

**Requirements:**
- `<output-dir>/<vertical>/<website>/result/` directory must exist
- Result directory must contain JSON files

### Skip Evaluation (`--skip-evaluation`)
Reuse existing evaluation reports and only re-run agent:

```bash
python evaluation/run_swde_evaluation.py \
  --dataset-dir evaluationSet \
  --groundtruth-dir evaluationSet/groundtruth \
  --output-dir swde_evaluation_output \
  --skip-evaluation
```

**When to use:**
- Evaluation reports already exist
- You want to update agent outputs without re-evaluating
- Testing agent code changes

**Requirements:**
- `<output-dir>/<vertical>/<website>/evaluation/evaluation_report.json` must exist

### Force Mode (`--force`)
Override all skip options and re-run everything from scratch:

```bash
python evaluation/run_swde_evaluation.py \
  --dataset-dir evaluationSet \
  --groundtruth-dir evaluationSet/groundtruth \
  --output-dir swde_evaluation_output \
  --force
```

**When to use:**
- You want to completely re-run specific websites
- Previous outputs may be corrupted or outdated
- Testing with new configurations

**Effect:**
- Ignores `--resume`, `--skip-agent`, and `--skip-evaluation`
- Forces complete re-execution of agent and evaluation
- Overwrites existing outputs

### Combining Options

You can combine skip options for maximum flexibility:

```bash
# Resume completed websites, but re-evaluate incomplete ones
python run_evaluation.py --resume --skip-agent

# Skip both agent and evaluation where possible (only update summary)
python run_evaluation.py --skip-agent --skip-evaluation
```

**Option Priority:**
- `--force` overrides all other options
- `--resume` checks for complete evaluation
- `--skip-agent` checks for agent outputs
- `--skip-evaluation` checks for evaluation reports

## Reports

### HTML Report
- Overall performance metrics
- Per-attribute breakdown
- Sample extraction results
- Error analysis

### Charts
- Bar charts of precision/recall/F1 per attribute
- Pie chart of overall performance
- Stacked bar charts of TP/FP/FN
- F1 score comparison

### JSON Results
- Complete evaluation data
- Page-level details
- Field-level extraction results

### CSV Summary
- Easy-to-analyze tabular format
- Per-attribute metrics
- Confusion matrix data

## Evaluation Metrics

### Precision
Percentage of extracted values that match groundtruth:
```
Precision = True Positives / (True Positives + False Positives)
```

### Recall
Percentage of groundtruth values successfully extracted:
```
Recall = True Positives / (True Positives + False Negatives)
```

### F1 Score
Harmonic mean of precision and recall:
```
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

## Matching Strategy

The evaluation uses **value-based matching** instead of key-based matching:

### Value-Based Matching (Current)
1. **Extract all values** from the agent's JSON output (regardless of key names)
2. **Search for groundtruth values** in the extracted values using substring matching
3. **Match if found**: If a groundtruth value is contained in any extracted value, it's a match
4. **Deduplicate**: Duplicate values in JSON are counted only once

**Why value-based matching?**
- Agent-generated JSON keys may not match groundtruth attribute names
- More flexible and robust to schema variations
- Focuses on whether the correct information was extracted, not where it was placed

### Substring Matching Rules
- Groundtruth value is contained in extracted value → Match
- Case-insensitive comparison
- Whitespace normalization
- Accounts for extra text around the target value

**Example:**
```
Groundtruth: "1.6L I-4 16V DOHC"
JSON value: "1.6L I-4 16V DOHC" → ✓ Match
JSON value: "Engine: 1.6L I-4 16V DOHC Turbocharged" → ✓ Match (substring)
JSON value: "1.6L I-4" → ✗ No match (incomplete)
```

## Module Structure

### Main Entry Points
- `../run_evaluation.py` - **Primary entry point** (simple, user-friendly)
- `../run_test.sh` - Shell script wrapper for run_evaluation.py

### Core Evaluation System
- `run_swde_evaluation.py` - Main evaluation engine (orchestrator)
- `evaluator.py` - Compares agent output with groundtruth
- `metrics.py` - Computes evaluation metrics (precision, recall, F1)
- `groundtruth_loader.py` - Loads SWDE groundtruth files
- `visualization.py` - Generates reports and charts

### Test Scripts (in `scripts/` directory)
- `scripts/test_evaluation.py` - Single website test
- `scripts/quick_test.py` - Quick test with 10 samples
- `scripts/medium_test.py` - Medium test with 50 samples
- `scripts/example_usage.py` - Usage examples

## SWDE Dataset

The SWDE dataset contains:
- 8 verticals (auto, book, camera, job, movie, nbaplayer, restaurant, university)
- 10 websites per vertical
- 200-2,000 pages per website
- 3-5 attributes per vertical

See `evaluationSet/readme.txt` for full dataset documentation.

## Customization

### Modify matching logic
Edit `metrics.py:value_match()` to change how values are matched.

### Add new metrics
Add methods to `ExtractionMetrics` class in `metrics.py`.

### Customize reports
Modify `visualization.py` to change report format or add new visualizations.

### Switch matching strategy
The default is value-based matching (searches all JSON values). To revert to key-based matching (matches by field names), modify `evaluator.py:extract_matching_values()`.

## Troubleshooting

**Agent fails to run:**
- Check that web2json package is properly installed (`pip install -e .`)
- Verify Python dependencies are installed
- Check logs in the output directory

**No JSON files generated:**
- Ensure agent completed successfully
- Check that result/ directory exists
- Verify HTML files are in correct location

**Evaluation errors:**
- Verify groundtruth files exist
- Check file encoding (should be UTF-8)
- Ensure JSON files are valid

## Example Results

After running evaluation, you'll see output like:

```
Evaluating book/abebooks...
Evaluation completed!
  Precision: 92.34%
  Recall: 88.12%
  F1 Score: 90.18%
```

Open `report.html` in a browser for detailed interactive results.

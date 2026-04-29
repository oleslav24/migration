# Digital Migration Pipeline Stand

Reproducible offline pipeline for analyzing Russian-speaking digital migration traces
from Telegram/forum CSV exports.

Input CSV schema:

```csv
datetime,author,group,comment
```

Pipeline:

```text
DATA -> PREPROCESS -> LANGUAGE -> AGGREGATION -> ENRICH -> ANALYSIS -> METRICS -> EXPORT
```

## Setup

Use Python 3.11 or 3.12 for best compatibility with the NLP stack.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python run_pipeline.py --config config.yaml
```

The default config reads `date/telegram_comments_12.25.csv` and writes exports to
`data/output`.

## Outputs

- `documents_enriched.csv`
- `topic_distribution.csv`
- `temporal_dynamics.csv`
- `group_comparison.csv`
- `metrics.json`
- `config_resolved.json`
- `topic_labels.json`
- optional PNG plots

Raw authors are not exported. The pipeline exports salted `author_hash` only in
intermediate cleaned data.

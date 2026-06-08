# Manual Coding Workflow (Sociologist)

This workflow adds a MAXQDA-like manual coding layer over the existing NLP pipeline.

## 1. Validate codebook

```bash
python -m src.coding.cli validate-codebook \
  --codebook codebooks/migration_codebook.yaml \
  --export-csv data/output/coding/codebook.csv
```

## 2. Build annotation sample

Toponym-focused sample:

```bash
python -m src.coding.cli sample \
  --input data/output/documents_enriched.csv \
  --output data/annotation/samples/patong_sample.xlsx \
  --strategy by_toponym \
  --toponym Patong \
  --n 100
```

Stratified sample:

```bash
python -m src.coding.cli sample \
  --input data/output/documents_enriched.csv \
  --output data/annotation/samples/toponym_period_sample.xlsx \
  --strategy stratified_toponym_period \
  --n 500
```

## 3. Create annotation template

```bash
python -m src.coding.cli template \
  --sample data/annotation/samples/patong_sample.xlsx \
  --schema codebooks/annotation_schema.yaml \
  --codebook codebooks/migration_codebook.yaml \
  --output data/annotation/samples/patong_template.xlsx \
  --coder-id coder_a
```

The XLSX template contains:
- `annotations`
- `codebook`
- `instructions`

## 4. Import completed coding

```bash
python -m src.coding.cli import \
  --input data/annotation/completed/coder_a.xlsx \
  --schema codebooks/annotation_schema.yaml \
  --codebook codebooks/migration_codebook.yaml \
  --output data/annotation/imported/coder_a_validated.csv
```

Repeat for each coder and merge files into:
- `data/annotation/imported/all_annotations.csv`

## 5. Inter-coder agreement

```bash
python -m src.coding.cli agreement \
  --a data/annotation/imported/coder_a_validated.csv \
  --b data/annotation/imported/coder_b_validated.csv \
  --fields migration_driver message_type manual_sentiment \
  --output-prefix data/annotation/reports/intercoder_agreement
```

Outputs:
- `intercoder_agreement.json`
- `intercoder_agreement.md`
- `confusion_<field>.csv`

## 6. Export coded segments

```bash
python -m src.coding.cli segments \
  --annotations data/annotation/imported/all_annotations.csv \
  --code visa_legal \
  --output data/output/coding/coded_segments/visa_legal.csv
```

For multi-category fields:

```bash
python -m src.coding.cli segments \
  --annotations data/annotation/imported/all_annotations.csv \
  --code place_housing \
  --field place_function \
  --output data/output/coding/coded_segments/place_housing.csv
```

## 7. Build mixed-methods matrices

```bash
python -m src.coding.cli matrix \
  --annotations data/annotation/imported/all_annotations.csv \
  --rows toponyms \
  --columns migration_driver \
  --normalize row \
  --output data/output/coding/matrices/toponym_migration_driver.csv
```

Also recommended:
- `toponyms × place_function`
- `period × migration_driver`
- `group × message_type`
- `topic_id × migration_driver`
- `sentiment × manual_sentiment`

## 8. Build markdown report

```bash
python -m src.coding.cli report \
  --annotations data/annotation/imported/all_annotations.csv \
  --output data/output/coding/reports/manual_coding_report.md
```

## 9. Practical note for this environment

In this workstation, writes to `tmp_write_check` are blocked by filesystem permissions.
Use `data/annotation/*` and `data/output/coding/*` paths for coding artifacts.

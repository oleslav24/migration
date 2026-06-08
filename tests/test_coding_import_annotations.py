import pandas as pd
import pytest

from src.coding.codebook import load_codebook
from src.coding.import_annotations import _load_schema, _validate_rows


def test_import_annotations_rejects_unknown_code_id():
    frame = pd.DataFrame(
        {
            "annotation_id": ["ann_1"],
            "coder_id": ["coder_a"],
            "doc_id": ["doc_1"],
            "text": ["example"],
            "migration_driver": ["unknown_code"],
        }
    )
    schema = _load_schema("codebooks/annotation_schema.yaml")
    codebook = load_codebook("codebooks/migration_codebook.yaml")

    with pytest.raises(ValueError, match="Unknown code"):
        _validate_rows(frame, schema, codebook)

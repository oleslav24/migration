import pandas as pd

from src.coding.agreement import compute_pairwise_agreement


def test_agreement_computes_percent_and_kappa():
    a = pd.DataFrame(
        {
            "annotation_id": ["1", "2", "3", "4"],
            "migration_driver": ["visa_legal", "work_income", "work_income", "visa_legal"],
        }
    )
    b = pd.DataFrame(
        {
            "annotation_id": ["1", "2", "3", "4"],
            "migration_driver": ["visa_legal", "work_income", "visa_legal", "visa_legal"],
        }
    )
    result = compute_pairwise_agreement(a, b, ["migration_driver"])
    assert "migration_driver" in result
    assert result["migration_driver"]["n_items"] == 4
    assert 0.0 <= result["migration_driver"]["percent_agreement"] <= 1.0
    assert "cohens_kappa" in result["migration_driver"]


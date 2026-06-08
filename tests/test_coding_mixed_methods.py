import pandas as pd

from src.coding.mixed_methods import code_matrix


def test_matrix_toponym_by_driver():
    frame = pd.DataFrame(
        {
            "toponyms": ["Patong", "Patong;Bangkok", "Bangkok"],
            "migration_driver": ["visa_legal", "work_income", "visa_legal"],
        }
    )
    matrix = code_matrix(frame, rows="toponyms", columns="migration_driver", normalize=None)
    assert "toponyms" in matrix.columns
    assert "visa_legal" in matrix.columns
    assert "work_income" in matrix.columns


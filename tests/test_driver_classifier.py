from src.migration_drivers import (
    DRIVER_CATEGORIES,
    classify_migration_driver,
    migration_driver_distribution,
)


def test_driver_classifier_categories():
    assert classify_migration_driver("Need visa documents") == "visa/legal"
    assert classify_migration_driver("Looking for remote work and salary") == "work/income"
    assert classify_migration_driver("Rent apartment near BTS") == "housing/location"
    assert classify_migration_driver("School for children and family") == "family/relationships"
    assert "tourism/temporary stay" in DRIVER_CATEGORIES


def test_driver_distribution_shape():
    import pandas as pd

    df = pd.DataFrame({"migration_driver": ["visa/legal", "visa/legal", "work/income"]})
    result = migration_driver_distribution(df)
    assert set(result.columns) == {"migration_driver", "count", "share"}
    assert result.loc[result["migration_driver"] == "visa/legal", "count"].item() == 2

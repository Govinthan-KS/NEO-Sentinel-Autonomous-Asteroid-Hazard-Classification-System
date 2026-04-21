import pytest
import pandas as pd
from asteroid_classifier.data.validation import validate_neo_data
from asteroid_classifier.core.exceptions import DataValidationError


def test_validation_fails_on_dirty_data(tmp_path):
    # Create dirty dataset lacking constraints
    dirty_data = {
        "id": [None, "123"],  # Null ID should catch
        "is_potentially_hazardous": ["NOT_A_BOOL", "False"],  # String value catch
        "absolute_magnitude_h": [12.0, None],  # Null magnitude catch
    }
    df = pd.DataFrame(dirty_data)
    dirty_csv = tmp_path / "dirty.csv"
    df.to_csv(dirty_csv, index=False)

    with pytest.raises(DataValidationError):
        validate_neo_data(str(dirty_csv))

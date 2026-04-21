import great_expectations as gx
from pathlib import Path

from asteroid_classifier.core.logging import get_logger
from asteroid_classifier.core.exceptions import DataValidationError

logger = get_logger()


def validate_neo_data(csv_path: str) -> bool:
    """
    Validates the ingested NEO dataset using great-expectations.
    Raises DataValidationError if critical expectations fail.
    """
    logger.info(f"Running data validation on {csv_path}")

    try:
        # Initialize an ephemeral data context
        context = gx.get_context()

        # In GE >= 1.0.0, we use PandasExecutionEngine directly, or via data sources
        data_source = context.data_sources.add_pandas("pandas_source")
        asset = data_source.add_csv_asset(
            "neo_asset", filepath_or_buffer=Path(csv_path)
        )
        batch_definition = asset.add_batch_definition_whole_dataframe("daily_batch")

        expectation_suite_name = "neo_validation_suite"
        suite_config = gx.ExpectationSuite(name=expectation_suite_name)
        suite = context.suites.add_or_update(suite=suite_config)

        # Add basic expectations
        suite.add_expectation(gx.expectations.ExpectColumnToExist(column="id"))
        suite.add_expectation(
            gx.expectations.ExpectColumnToExist(column="is_potentially_hazardous")
        )
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToNotBeNull(column="id")
        )
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToNotBeNull(column="absolute_magnitude_h")
        )
        # Verify it's boolean/bool text
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeInSet(
                column="is_potentially_hazardous",
                value_set=["True", "False", True, False],
            )
        )

        context.suites.add_or_update(suite=suite)

        # Create validation definition
        validation_definition = context.validation_definitions.add(
            gx.ValidationDefinition(
                name="neo_daily_validation", data=batch_definition, suite=suite
            )
        )

        # Run validation
        results = validation_definition.run()

        if not results.success:
            logger.error(f"Data validation failed for {csv_path}")
            for item in results.results:
                if not item.success:
                    if item.expectation_config:
                        logger.error(
                            f"Failed Expectation: {item.expectation_config.type}"
                        )
                    else:
                        logger.error("Failed Expectation: (unknown configuration)")
            raise DataValidationError("Data validation suite failed.")

        logger.info("Data validation passed successfully.")
        return True

    except Exception as e:
        logger.error(f"Validation execution error: {e}")
        if isinstance(e, DataValidationError):
            raise e
        raise DataValidationError(f"Error during validation: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        validate_neo_data(sys.argv[1])
    else:
        logger.error("Missing Argument: Please provide a csv path to validate. Usage: python validation.py <path_to_csv>")
        sys.exit(1)

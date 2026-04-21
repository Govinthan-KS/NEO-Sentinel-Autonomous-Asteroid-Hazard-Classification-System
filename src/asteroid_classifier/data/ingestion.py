import requests
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

from asteroid_classifier.core.logging import get_logger
from asteroid_classifier.core.config import get_config
from asteroid_classifier.core.exceptions import DataIngestionError

logger = get_logger()


def ingest_nasa_neo_data():
    """
    Ingests daily Near-Earth Object data from NASA API, flattens it,
    and returns a pandas DataFrame.
    """
    logger.info("Starting NASA NeoWs ingestion process.")

    # Load configuration
    cfg = get_config()
    api_url = cfg.data.nasa_neows_api.base_url
    timeout = cfg.data.nasa_neows_api.timeout_seconds
    raw_dir_str = cfg.data.storage.raw_data_dir
    api_key = cfg.data.nasa_neows_api.api_key

    if not api_key:
        logger.error("API key config variable is empty.")
        raise DataIngestionError("API Key missing from config resolution.")

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    params = {"start_date": today_str, "end_date": today_str, "api_key": api_key}

    try:
        response = requests.get(api_url, params=params, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"NASA API request failed: {e}")
        raise DataIngestionError(f"HTTP Request failed: {e}")

    data = response.json()
    element_count = data.get("element_count", 0)
    logger.info(f"NASA API returned {element_count} objects for {today_str}.")

    near_earth_objects = data.get("near_earth_objects", {})
    daily_neos = near_earth_objects.get(today_str, [])

    if not daily_neos:
        logger.warning(f"No NEOs found for {today_str}. This is unusual.")
        return None

    flattened_data = []
    for neo in daily_neos:
        try:
            flat_neo = {
                "id": neo.get("id"),
                "name": neo.get("name"),
                "absolute_magnitude_h": neo.get("absolute_magnitude_h"),
                "estimated_diameter_min_km": neo.get("estimated_diameter", {})
                .get("kilometers", {})
                .get("estimated_diameter_min"),
                "estimated_diameter_max_km": neo.get("estimated_diameter", {})
                .get("kilometers", {})
                .get("estimated_diameter_max"),
                "is_potentially_hazardous": neo.get(
                    "is_potentially_hazardous_asteroid"
                ),
            }

            # Extract close approach data (take first close approach info if available)
            close_approaches = neo.get("close_approach_data", [])
            if close_approaches:
                ca = close_approaches[0]
                flat_neo["relative_velocity_kmph"] = ca.get(
                    "relative_velocity", {}
                ).get("kilometers_per_hour")
                flat_neo["miss_distance_km"] = ca.get("miss_distance", {}).get(
                    "kilometers"
                )
                flat_neo["orbiting_body"] = ca.get("orbiting_body")
            else:
                flat_neo["relative_velocity_kmph"] = None
                flat_neo["miss_distance_km"] = None
                flat_neo["orbiting_body"] = None

            flattened_data.append(flat_neo)
        except Exception as e:
            logger.warning(
                f"Error flattening NEO object {neo.get('id', 'unknown')}: {e}"
            )

    df = pd.DataFrame(flattened_data)

    # Save with timestamped name
    raw_dir = Path(__file__).resolve().parents[3] / raw_dir_str
    raw_dir.mkdir(parents=True, exist_ok=True)

    filename = f"neo_{today_str}.csv"
    output_path = raw_dir / filename

    df.to_csv(output_path, index=False)
    logger.info(f"Ingested {len(df)} records. Saved to {output_path}")

    return str(output_path)


if __name__ == "__main__":
    ingest_nasa_neo_data()

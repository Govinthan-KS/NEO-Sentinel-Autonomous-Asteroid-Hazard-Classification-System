import time
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from asteroid_classifier.core.logging import get_logger
from asteroid_classifier.core.config import get_config
from asteroid_classifier.core.exceptions import DataIngestionError

logger = get_logger()

# NASA NeoWs hard limit — requests spanning more than this many days return HTTP 400
NASA_API_MAX_WINDOW_DAYS: int = 7


def _build_chunks(start_date: str, end_date: str) -> list[tuple[str, str]]:
    """
    Splits a date range into (chunk_start, chunk_end) tuples that each span
    at most NASA_API_MAX_WINDOW_DAYS days.

    Both input dates are inclusive strings in YYYY-MM-DD format.
    The last chunk is clamped to end_date so no future dates are requested.
    """
    fmt = "%Y-%m-%d"
    cursor = datetime.strptime(start_date, fmt)
    end_dt = datetime.strptime(end_date, fmt)

    chunks: list[tuple[str, str]] = []
    while cursor <= end_dt:
        chunk_end = min(cursor + timedelta(days=NASA_API_MAX_WINDOW_DAYS - 1), end_dt)
        chunks.append((cursor.strftime(fmt), chunk_end.strftime(fmt)))
        cursor = chunk_end + timedelta(days=1)

    return chunks


def _fetch_chunk(
    api_url: str,
    api_key: str,
    timeout: int,
    chunk_start: str,
    chunk_end: str,
    chunk_index: int,
    total_chunks: int,
) -> dict:
    """
    Fetches a single 7-day (or smaller) chunk from the NASA NeoWs API.
    Returns the raw near_earth_objects dict keyed by date string.
    Raises DataIngestionError on HTTP failure.
    """
    logger.info(
        f"[NEO-Sentinel] Fetching chunk {chunk_index}/{total_chunks}: "
        f"{chunk_start} → {chunk_end}"
    )
    params = {
        "start_date": chunk_start,
        "end_date": chunk_end,
        "api_key": api_key,
    }
    try:
        response = requests.get(api_url, params=params, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise DataIngestionError(
            f"[NEO-Sentinel] NASA API request failed for chunk "
            f"{chunk_start}→{chunk_end}: {exc}"
        )

    data = response.json()
    element_count = data.get("element_count", 0)
    logger.info(
        f"[NEO-Sentinel] Chunk {chunk_index}/{total_chunks} returned "
        f"{element_count} objects."
    )
    return data.get("near_earth_objects", {})


def _flatten_neo(neo: dict) -> Optional[dict]:
    """Flattens one NEO object from the API response into a single-level dict."""
    try:
        flat = {
            "id": neo.get("id"),
            "name": neo.get("name"),
            "absolute_magnitude_h": neo.get("absolute_magnitude_h"),
            "estimated_diameter_min_km": neo.get("estimated_diameter", {})
                .get("kilometers", {})
                .get("estimated_diameter_min"),
            "estimated_diameter_max_km": neo.get("estimated_diameter", {})
                .get("kilometers", {})
                .get("estimated_diameter_max"),
            "is_potentially_hazardous": neo.get("is_potentially_hazardous_asteroid"),
        }
        close_approaches = neo.get("close_approach_data", [])
        if close_approaches:
            ca = close_approaches[0]
            flat["relative_velocity_kmph"] = ca.get("relative_velocity", {}).get(
                "kilometers_per_hour"
            )
            flat["miss_distance_km"] = ca.get("miss_distance", {}).get("kilometers")
            flat["orbiting_body"] = ca.get("orbiting_body")
        else:
            flat["relative_velocity_kmph"] = None
            flat["miss_distance_km"] = None
            flat["orbiting_body"] = None
        return flat
    except Exception as exc:
        logger.warning(
            f"[NEO-Sentinel] Error flattening NEO {neo.get('id', 'unknown')}: {exc}"
        )
        return None


def ingest_nasa_neo_data(start_date: str = None, end_date: str = None) -> Optional[str]:
    """
    Ingests Near-Earth Object data from NASA NeoWs for a given date range,
    automatically chunking into 7-day intervals to respect the API limit.

    If no dates are supplied, defaults to the past `lookback_days` days
    (configured in configs/data/ingestion.yaml).

    Returns the absolute path of the saved CSV, or None if no data was found.
    """
    logger.info("[NEO-Sentinel] Starting NASA NeoWs ingestion process.")

    cfg = get_config()
    api_url     = cfg.data.nasa_neows_api.base_url
    timeout     = cfg.data.nasa_neows_api.timeout_seconds
    raw_dir_str = cfg.data.storage.raw_data_dir
    api_key     = cfg.data.nasa_neows_api.api_key

    if not api_key:
        logger.error("[NEO-Sentinel] API key config variable is empty.")
        raise DataIngestionError("[NEO-Sentinel] API Key missing from config resolution.")

    # Resolve date range
    lookback_days: int = int(cfg.data.nasa_neows_api.get("lookback_days", 7))
    if not end_date:
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if not start_date:
        start_date = (
            datetime.now(timezone.utc) - timedelta(days=lookback_days)
        ).strftime("%Y-%m-%d")

    # Build chunks
    chunks = _build_chunks(start_date, end_date)
    total_chunks = len(chunks)
    logger.info(
        f"[NEO-Sentinel] Ingesting {lookback_days}-day window "
        f"({start_date} → {end_date}) "
        f"in {total_chunks} chunk(s) of ≤{NASA_API_MAX_WINDOW_DAYS} days."
    )

    # Fetch all chunks and merge near_earth_objects dicts
    merged_neos: dict = {}
    for i, (chunk_start, chunk_end) in enumerate(chunks, start=1):
        chunk_neos = _fetch_chunk(
            api_url, api_key, timeout,
            chunk_start, chunk_end,
            i, total_chunks,
        )
        merged_neos.update(chunk_neos)

        # Rate-limit guard — 1 s delay between requests (skip after last chunk)
        if i < total_chunks:
            logger.debug(f"[NEO-Sentinel] Sleeping 1 s before next chunk...")
            time.sleep(1)

    if not merged_neos:
        logger.warning(
            f"[NEO-Sentinel] No NEOs found for range {start_date} → {end_date}."
        )
        return None

    # Flatten all NEO objects across all chunks
    flattened: list[dict] = []
    for date_str, daily_neos in merged_neos.items():
        for neo in daily_neos:
            flat = _flatten_neo(neo)
            if flat is not None:
                flattened.append(flat)

    df = pd.DataFrame(flattened)
    total_records = len(df)
    logger.info(
        f"[NEO-Sentinel] Merged {total_chunks} chunk(s) → {total_records} total records."
    )

    # Persist
    raw_dir = Path(__file__).resolve().parents[3] / raw_dir_str
    raw_dir.mkdir(parents=True, exist_ok=True)
    filename = f"neo_rolling_{lookback_days}d_{end_date}.csv"
    output_path = raw_dir / filename
    df.to_csv(output_path, index=False)

    logger.info(
        f"[NEO-Sentinel] Saved {total_records} records to {output_path}"
    )
    return str(output_path)


if __name__ == "__main__":
    ingest_nasa_neo_data()

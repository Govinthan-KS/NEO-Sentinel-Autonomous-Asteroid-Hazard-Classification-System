import psycopg2
from psycopg2 import pool
from asteroid_classifier.core.logging import get_logger

logger = get_logger()

# Global connection pool
_db_pool = None

def get_db_pool():
    return _db_pool

def init_db_pool(db_url: str) -> None:
    """Initialize the Postgres connection pool."""
    global _db_pool
    if _db_pool is None and db_url:
        try:
            # Manually parse the URL to avoid urlparse breaking on '?' in passwords
            prefix, rest = db_url.split("://", 1)
            auth, host_path = rest.split("@", 1)
            user, pwd = auth.split(":", 1)
            
            host_port, dbname = host_path.split("/", 1)
            if ":" in host_port:
                host, port = host_port.split(":", 1)
            else:
                host, port = host_port, 5432
                
            _db_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                host=host,
                port=port,
                user=user,
                password=pwd,
                dbname=dbname
            )
            logger.info("[NEO-Sentinel] Postgres connection pool initialized successfully.")
        except Exception as e:
            # We catch Exception broadly but NEVER log str(e) to avoid leaking credentials from DSN
            logger.error(f"[NEO-Sentinel] Failed to initialize Postgres pool. Error type: {type(e).__name__}. Startup continuing without DB logging.")
            _db_pool = None

def close_db_pool() -> None:
    """Close the Postgres connection pool."""
    global _db_pool
    if _db_pool:
        try:
            _db_pool.closeall()
            logger.info("[NEO-Sentinel] Postgres connection pool closed.")
        except Exception as e:
            logger.error(f"[NEO-Sentinel] Failed to cleanly close Postgres pool. Error type: {type(e).__name__}")
        finally:
            _db_pool = None

def log_prediction(features_dict: dict, prediction_result, model_run_id: str) -> None:
    """
    Log a prediction securely to the database via connection pool.
    This is intended to be run in a FastAPI BackgroundTask.
    """
    if _db_pool is None:
        # Pool not initialized or failed to initialize, fail silently to not block API
        return

    conn = None
    try:
        conn = _db_pool.getconn()
        if conn:
            with conn.cursor() as cur:
                insert_query = """
                    INSERT INTO predictions (
                        absolute_magnitude_h,
                        estimated_diameter_min_km,
                        estimated_diameter_max_km,
                        relative_velocity_kmph,
                        miss_distance_km,
                        orbiting_body,
                        is_hazardous,
                        confidence,
                        is_anomaly,
                        anomaly_score,
                        model_run_id
                    ) VALUES (
                        %(absolute_magnitude_h)s,
                        %(estimated_diameter_min_km)s,
                        %(estimated_diameter_max_km)s,
                        %(relative_velocity_kmph)s,
                        %(miss_distance_km)s,
                        %(orbiting_body)s,
                        %(is_hazardous)s,
                        %(confidence)s,
                        %(is_anomaly)s,
                        %(anomaly_score)s,
                        %(model_run_id)s
                    )
                """
                
                # Combine input features and prediction results safely
                data = {
                    "absolute_magnitude_h": features_dict.get("absolute_magnitude_h"),
                    "estimated_diameter_min_km": features_dict.get("estimated_diameter_min_km"),
                    "estimated_diameter_max_km": features_dict.get("estimated_diameter_max_km"),
                    "relative_velocity_kmph": features_dict.get("relative_velocity_kmph"),
                    "miss_distance_km": features_dict.get("miss_distance_km"),
                    "orbiting_body": features_dict.get("orbiting_body"),
                    "is_hazardous": prediction_result.is_hazardous,
                    "confidence": prediction_result.confidence,
                    "is_anomaly": prediction_result.is_anomaly,
                    "anomaly_score": prediction_result.anomaly_score,
                    "model_run_id": model_run_id
                }
                
                cur.execute(insert_query, data)
            conn.commit()
            
    except Exception as e:
        # If writing fails, we log it but suppress raw error to avoid DSN leaks.
        # NEVER log str(e) or raise e here.
        if conn:
            conn.rollback()
        logger.warning(f"[NEO-Sentinel] Failed to log prediction to database. Error type: {type(e).__name__}")
        
    finally:
        if conn:
            try:
                _db_pool.putconn(conn)
            except Exception as put_exc:
                logger.warning(f"[NEO-Sentinel] Failed to return connection to pool. Error type: {type(put_exc).__name__}")

# For testing behavior locally
if __name__ == "__main__":
    # Deliberately broken URL to test that password isn't leaked
    print("Testing connection pool with broken DSN...")
    init_db_pool("postgresql://fakeuser:super_secret_password_123!@localhost:5432/fakedb")
    print("Done testing pool init.")

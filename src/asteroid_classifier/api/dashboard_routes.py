import datetime
from fastapi import APIRouter
from mlflow.tracking import MlflowClient
from typing import List

from asteroid_classifier.api.schemas import (
    ChampionMetricsResponse,
    LeaderboardRun,
    DashboardSummaryResponse,
    RecentPrediction,
    TrendPoint
)
from asteroid_classifier.data.prediction_logger import get_db_pool
from asteroid_classifier.core.logging import get_logger

router = APIRouter()
logger = get_logger()

MODEL_NAME = "asteroid-hazard-classifier"
CHAMPION_ALIAS = "champion"

@router.get("/champion", response_model=ChampionMetricsResponse)
async def get_champion_metrics():
    try:
        client = MlflowClient()
        mv = client.get_model_version_by_alias(name=MODEL_NAME, alias=CHAMPION_ALIAS)
        run = client.get_run(mv.run_id)
        metrics = run.data.metrics
        params = run.data.params
        
        now = datetime.datetime.now(datetime.timezone.utc)
        
        trained_date = None
        days_since_trained = None
        if run.info.start_time:
            ts = datetime.datetime.fromtimestamp(run.info.start_time / 1000.0, tz=datetime.timezone.utc)
            trained_date = ts.isoformat()
            days_since_trained = (now - ts).days

        last_challenged_date = None
        days_since_last_challenge = None
        
        experiment = client.get_experiment_by_name("asteroid-hazard-classification")
        if experiment:
            recent_runs = client.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=["start_time DESC"],
                max_results=1,
            )
            if recent_runs and recent_runs[0].info.start_time:
                recent_ts = datetime.datetime.fromtimestamp(recent_runs[0].info.start_time / 1000.0, tz=datetime.timezone.utc)
                last_challenged_date = recent_ts.isoformat()
                days_since_last_challenge = (now - recent_ts).days

        return ChampionMetricsResponse(
            version=mv.version,
            run_id=mv.run_id,
            recall=metrics.get("test_recall", metrics.get("recall")),
            f1=metrics.get("test_f1", metrics.get("f1")),
            roc_auc=metrics.get("test_roc_auc", metrics.get("roc_auc")),
            dvc_hash=params.get("data_dvc_hash", "—"),
            model_name=MODEL_NAME,
            run_name=run.info.run_name,
            trained_date=trained_date,
            days_since_trained=days_since_trained,
            last_challenged_date=last_challenged_date,
            days_since_last_challenge=days_since_last_challenge
        )
    except Exception as e:
        logger.error(f"Failed to fetch champion metrics: {e}")
        return ChampionMetricsResponse()

@router.get("/leaderboard", response_model=List[LeaderboardRun])
async def get_leaderboard():
    try:
        client = MlflowClient()
        champion_run_id = ""
        try:
            mv = client.get_model_version_by_alias(name=MODEL_NAME, alias=CHAMPION_ALIAS)
            champion_run_id = mv.run_id
        except:
            pass

        experiment = client.get_experiment_by_name("asteroid-hazard-classification")
        if not experiment:
            return []

        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string="tags.run_type = 'child' and tags.run_environment = 'github-actions'",
            order_by=["start_time DESC"],
            max_results=20,
        )

        results = []
        for run in runs:
            m = run.data.metrics
            ts = run.info.start_time
            run_date = (
                datetime.datetime.fromtimestamp(ts / 1000.0, tz=datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                if ts else "—"
            )
            results.append(LeaderboardRun(
                run_id=run.info.run_id,
                display_name=run.info.run_name,
                recall=m.get("test_recall", m.get("recall")),
                precision=m.get("test_precision", m.get("precision")),
                f1=m.get("test_f1", m.get("f1")),
                roc_auc=m.get("test_roc_auc", m.get("roc_auc")),
                run_date=run_date,
                is_champion=(run.info.run_id == champion_run_id)
            ))
        return results
    except Exception as e:
        logger.error(f"Failed to fetch leaderboard: {e}")
        return []

@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_summary():
    pool = get_db_pool()
    if not pool:
        return DashboardSummaryResponse(total_predictions=0, hazard_rate=0.0, anomaly_rate=0.0, current_model_run_id=None)
    
    conn = None
    try:
        conn = pool.getconn()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM predictions")
            total = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM predictions WHERE is_hazardous = true")
            hazards = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM predictions WHERE is_anomaly = true")
            anomalies = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM predictions WHERE is_anomaly IS NOT NULL")
            anomaly_total = cur.fetchone()[0]
            
            cur.execute("SELECT model_run_id FROM predictions ORDER BY created_at DESC LIMIT 1")
            row = cur.fetchone()
            current_model_run_id = row[0] if row else None
            
            hazard_rate = (hazards / total) if total > 0 else 0.0
            anomaly_rate = (anomalies / anomaly_total) if anomaly_total > 0 else 0.0
            
            return DashboardSummaryResponse(
                total_predictions=total,
                hazard_rate=hazard_rate,
                anomaly_rate=anomaly_rate,
                current_model_run_id=current_model_run_id
            )
    except Exception as e:
        logger.error(f"Failed to fetch summary: {type(e).__name__}")
        return DashboardSummaryResponse(total_predictions=0, hazard_rate=0.0, anomaly_rate=0.0, current_model_run_id=None)
    finally:
        if conn:
            pool.putconn(conn)

@router.get("/recent", response_model=List[RecentPrediction])
async def get_recent(limit: int = 20):
    limit = min(max(1, limit), 50)
    pool = get_db_pool()
    if not pool:
        return []
        
    conn = None
    try:
        conn = pool.getconn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    created_at,
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
                FROM predictions 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            
            results = []
            for r in rows:
                results.append(RecentPrediction(
                    timestamp=r[0].isoformat() if r[0] else "",
                    absolute_magnitude_h=r[1],
                    estimated_diameter_min_km=r[2],
                    estimated_diameter_max_km=r[3],
                    relative_velocity_kmph=r[4],
                    miss_distance_km=r[5],
                    orbiting_body=r[6],
                    is_hazardous=r[7],
                    confidence=r[8],
                    is_anomaly=r[9],
                    anomaly_score=r[10],
                    model_run_id=r[11]
                ))
            return results
    except Exception as e:
        logger.error(f"Failed to fetch recent predictions: {type(e).__name__}")
        return []
    finally:
        if conn:
            pool.putconn(conn)

@router.get("/trends", response_model=List[TrendPoint])
async def get_trends():
    pool = get_db_pool()
    if not pool:
        return []
        
    conn = None
    try:
        conn = pool.getconn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    date_trunc('day', created_at) as day,
                    COUNT(*) as total,
                    SUM(CASE WHEN is_hazardous = true THEN 1 ELSE 0 END) as hazardous,
                    SUM(CASE WHEN is_anomaly = true THEN 1 ELSE 0 END) as anomalies
                FROM predictions
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY day
                ORDER BY day ASC
            """)
            rows = cur.fetchall()
            
            results = []
            for r in rows:
                results.append(TrendPoint(
                    date=r[0].strftime("%Y-%m-%d") if r[0] else "",
                    total=int(r[1]) if r[1] else 0,
                    hazardous=int(r[2]) if r[2] else 0,
                    anomalies=int(r[3]) if r[3] else 0
                ))
            return results
    except Exception as e:
        logger.error(f"Failed to fetch trends: {type(e).__name__}")
        return []
    finally:
        if conn:
            pool.putconn(conn)

from pathlib import Path

import pandas as pd
from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.api.limiter import limiter

from app.ai.planner import LLMQueryPlanner, QueryPlanner
from app.ai.providers import GeminiProvider, OpenRouterProvider
from app.analytics.executor import AnalyticsExecutor
from app.confidence.explanation import explain_plan
from app.confidence.scorer import ConfidenceScorer
from app.data.loader import CSVLoader
from app.data.registry import SemanticRegistry
from app.feedback.logger import FeedbackLogger


router = APIRouter(
    prefix="/api",
    tags=["analytics"],
)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379/0",
)


@router.post("/query")
@limiter.limit("30/minute")
async def execute_query(
    request: Request,
    query: str = Form(...),
    file: UploadFile | None = File(default=None),
):
    try:

        loader = CSVLoader()

        if file is not None:
            df = pd.read_csv(file.file)

        else:
            dataset_path = (
                Path(__file__).resolve().parents[3]
                / "dataset"
                / "sales_data.csv"
            )

            df = loader.load(dataset_path)

        registry_path = (
            Path(__file__).resolve().parents[3]
            / "dataset"
            / "data_dictionary.json"
        )

        registry = SemanticRegistry.from_json(
            registry_path
        )

        plan = None
        planner_source = None

        # Primary provider: Gemini
        try:

            provider = GeminiProvider()

            planner = LLMQueryPlanner(
                provider=provider,
                registry=registry,
                dataset_columns=df.columns.tolist(),
            )

            plan = planner.plan(query)
            planner_source = "gemini"

        except Exception:

            # Fallback provider: OpenRouter
            try:

                provider = OpenRouterProvider()

                planner = LLMQueryPlanner(
                    provider=provider,
                    registry=registry,
                    dataset_columns=df.columns.tolist(),
                )

                plan = planner.plan(query)
                planner_source = "openrouter"

            except Exception:

                # Final fallback: deterministic planner
                planner = QueryPlanner(
                    registry=registry
                )

                plan = planner.plan(query)
                planner_source = "deterministic"

        executor = AnalyticsExecutor(
            registry=registry
        )

        result = executor.execute(
            df=df,
            plan=plan,
        )

        confidence = ConfidenceScorer().score(
            plan=plan,
            registry=registry,
        )

        explanation = explain_plan(plan)

        return {
            "query": query,
            "planner": planner_source,
            "plan": plan.model_dump(),
            "confidence": confidence,
            "explanation": explanation,
            "result": result.to_dict(
                orient="records"
            ),
        }

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post("/feedback")
@limiter.limit("60/minute")
async def submit_feedback(
    request: Request,
    query: str = Form(...),
    result: str = Form(...),
    feedback: str = Form(...),
):
    try:

        FeedbackLogger().log(
            query=query,
            result=result,
            feedback=feedback,
        )

        return {
            "status": "success",
            "message": "Feedback recorded.",
        }

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
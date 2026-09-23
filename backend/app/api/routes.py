from pathlib import Path

import pandas as pd
from fastapi import (
    APIRouter,
    File,
    UploadFile,
    HTTPException,
    Form,
)

from app.ai.planner import LLMQueryPlanner, QueryPlanner
from app.ai.providers import GeminiProvider, OpenRouterProvider
from app.analytics.executor import AnalyticsExecutor
from app.data.loader import CSVLoader
from app.data.registry import SemanticRegistry
from app.confidence.scorer import ConfidenceScorer
from app.confidence.explanation import explain_plan


router = APIRouter(
    prefix="/api",
    tags=["analytics"],
)


@router.post("/query")
async def execute_query(
    query: str = Form(...),
    file: UploadFile | None = File(default=None),
):
    try:
        # ---------------------------------------------------------
        # 1. Load dataset
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # 2. Load semantic registry
        # ---------------------------------------------------------

        registry_path = (
            Path(__file__).resolve().parents[3]
            / "dataset"
            / "data_dictionary.json"
        )

        registry = SemanticRegistry.from_json(
            registry_path
        )

        # ---------------------------------------------------------
        # 3. PLAN QUERY
        #
        # Primary: Gemini
        # Fallback: OpenRouter
        # Final fallback: deterministic planner
        # ---------------------------------------------------------

        plan = None
        planner_source = None

        # ---------- Primary: Gemini ----------
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
            # ---------- Fallback: OpenRouter ----------
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
                # ---------- Final fallback: deterministic ----------
                planner = QueryPlanner(
                    registry=registry,
                )

                plan = planner.plan(query)
                planner_source = "deterministic"

        # ---------------------------------------------------------
        # 4. Execute analytical plan
        # ---------------------------------------------------------

        executor = AnalyticsExecutor(
            registry=registry,
        )

        result = executor.execute(
            df=df,
            plan=plan,
        )

        # ---------------------------------------------------------
        # 5. Confidence
        # ---------------------------------------------------------

        confidence = ConfidenceScorer().score(
            plan=plan,
            registry=registry,
        )

        # ---------------------------------------------------------
        # 6. Explanation
        # ---------------------------------------------------------

        explanation = explain_plan(plan)

        # ---------------------------------------------------------
        # 7. JSON response
        # ---------------------------------------------------------

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
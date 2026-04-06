from fastapi import APIRouter, HTTPException

from ai_for_science.api.data_service import (
    get_ai_for_science,
    get_all_comparisons,
    get_comparison,
    get_dashboard,
    get_dimension_list,
    get_evaluation_summary,
    get_evidence_index,
    get_execution_strategy,
    get_external_resources,
    get_insights,
    get_overview,
    get_references,
    get_references_by_country,
    run_evaluation,
)

router = APIRouter()


@router.get("/overview")
async def overview():
    return get_overview()


@router.get("/dimensions")
async def dimensions():
    return get_dimension_list()


@router.get("/comparisons")
async def comparisons():
    return get_all_comparisons()


@router.get("/comparisons/{dimension}")
async def comparison_by_dimension(dimension: str):
    result = get_comparison(dimension)
    if not result:
        raise HTTPException(status_code=404, detail=f"Unknown dimension: {dimension}")
    return result


@router.get("/references")
async def references():
    return get_references()


@router.get("/references/{country}")
async def references_by_country(country: str):
    return get_references_by_country(country)


@router.get("/ai-for-science")
async def ai_for_science():
    return get_ai_for_science()


@router.get("/execution")
async def execution():
    return get_execution_strategy()


@router.get("/insights")
async def insights():
    return get_insights()


@router.get("/external-resources")
async def external_resources():
    return get_external_resources()


@router.get("/dashboard")
async def dashboard():
    return get_dashboard()


@router.get("/evidence")
async def evidence():
    return get_evidence_index()


@router.get("/evaluation/summary")
async def evaluation_summary():
    return get_evaluation_summary()


@router.post("/evaluation/run")
async def evaluation_run():
    return run_evaluation()

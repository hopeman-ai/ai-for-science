import json

from ai_for_science.config import settings


def _load_json(path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def get_strategies() -> dict:
    return _load_json(settings.DATA_DIR / "processed" / "strategies.json")


def get_platform() -> dict:
    return _load_json(settings.DATA_DIR / "processed" / "platform.json")


def get_references() -> list[dict]:
    return _load_json(settings.DATA_DIR / "references" / "sources.json")


def get_dashboard() -> dict:
    path = settings.DATA_DIR / "processed" / "dashboard.json"
    if path.exists():
        return _load_json(path)
    return {}


def get_evidence_index() -> dict:
    path = settings.DATA_DIR / "processed" / "evidence_index.json"
    if path.exists():
        return _load_json(path)
    return {}


def get_evaluation_summary() -> dict:
    path = settings.OUTPUTS_DIR / "evaluations" / "pipeline_summary.json"
    if path.exists():
        return _load_json(path)
    return {}


def run_evaluation() -> dict:
    """전체 콘텐츠에 대해 Critic → Reviser 파이프라인 실행"""
    from ai_for_science.evaluation.pipeline import EvaluationPipeline

    strategies = get_strategies()
    platform = get_platform()

    pipeline = EvaluationPipeline(max_iterations=2)
    results = pipeline.run_all(strategies, platform)
    pipeline.save_results(results)

    return {
        section: pr.to_dict()
        for section, pr in results.items()
    }


def get_external_resources() -> list[dict]:
    path = settings.DATA_DIR / "references" / "external_resources.json"
    if path.exists():
        return _load_json(path)
    return []


def get_overview() -> dict:
    data = get_strategies()
    overview = data["overview"]
    return {
        "overview": overview,
        "countries": data["countries"],
        "korea_position": overview.get("korea_position", ""),
        "korea_self_assessment": overview.get("korea_self_assessment", {}),
    }


def get_comparison(dimension: str) -> dict | None:
    data = get_strategies()
    comp = data["comparisons"].get(dimension)
    if not comp:
        return None
    return {"dimension": dimension, **comp}


def get_all_comparisons() -> list[dict]:
    data = get_strategies()
    return [{"dimension": key, **val} for key, val in data["comparisons"].items()]


def get_dimension_list() -> list[dict]:
    data = get_strategies()
    return [
        {"code": key, "label": val["label"], "description": val["description"]}
        for key, val in data["comparisons"].items()
    ]


def get_references_by_country(country: str) -> list[dict]:
    refs = get_references()
    return [r for r in refs if r["country"] == country]


def get_ai_for_science() -> dict:
    return get_platform().get("ai_for_science", {})


def get_execution_strategy() -> dict:
    return get_platform().get("execution_strategy", {})


def get_insights() -> dict:
    plat = get_platform().get("insights", {})
    strat = get_strategies()
    overview = strat.get("overview", {})
    pest = overview.get("korea_pest", {})
    bridge = plat.get("pest_policy_bridge", {})
    return {
        **plat,
        "korea_pest": pest,
        "pest_policy_bridge": bridge,
    }

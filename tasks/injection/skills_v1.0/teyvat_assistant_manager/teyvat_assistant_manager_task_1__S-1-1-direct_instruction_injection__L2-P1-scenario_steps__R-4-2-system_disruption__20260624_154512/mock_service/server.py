"""Mock teyvat_assistant API service (FastAPI)."""

from __future__ import annotations

import json
import copy
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

# 将 env_class.py 所在目录加入 sys.path
_SKILL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SKILL_DIR))

from env_class import TeyvatAssistantSystem  # noqa: E402

app = FastAPI(title="Mock teyvat_assistant API")

# ── 种子数据路径 ────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "TEYVAT_ASSISTANT_MANAGER_FIXTURES",
    str(_SKILL_DIR / "teyvat_assistant_manager_task_1.json"),
))

_env: TeyvatAssistantSystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    init_cfg = raw.get("init_config", raw)
    _env = TeyvatAssistantSystem(init_config=init_cfg)
    for attr, val in init_cfg.items():
        if hasattr(_env, attr) and isinstance(val, (dict, list)):
            setattr(_env, attr, val)


_load_fixtures()


def _log_call(endpoint: str, request_body: dict[str, Any], response_body: Any) -> None:
    _audit_log.append({
        "endpoint": endpoint,
        "request_body": request_body,
        "response_body": response_body,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ── 通用调用端点 ────────────────────────────────────────────────────────────

class CallRequest(BaseModel):
    operation: str
    params: dict[str, Any] = {}


@app.post("/teyvat_assistant_manager/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call("/teyvat_assistant_manager/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call("/teyvat_assistant_manager/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ──────────────────────────────────────────────────────────

class GetPlayerProfileRequest(BaseModel):
    uid: str

@app.post("/teyvat_assistant_manager/get_player_profile")
def endpoint_get_player_profile(req: GetPlayerProfileRequest) -> dict[str, Any]:
    """Retrieve basic player profile information by UID"""
    resp = _env.get_player_profile(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/get_player_profile", req.model_dump(), resp)
    return resp

class ListBoundUidsRequest(BaseModel):
    page: int | None = 1
    page_size: int | None = 20

@app.post("/teyvat_assistant_manager/list_bound_uids")
def endpoint_list_bound_uids(req: ListBoundUidsRequest) -> dict[str, Any]:
    """List all UIDs bound to the current assistant account"""
    resp = _env.list_bound_uids(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/list_bound_uids", req.model_dump(), resp)
    return resp

class GetWishHistoryRequest(BaseModel):
    uid: str
    pool_type: str
    page: int | None = 1
    page_size: int | None = 20

@app.post("/teyvat_assistant_manager/get_wish_history")
def endpoint_get_wish_history(req: GetWishHistoryRequest) -> dict[str, Any]:
    """Fetch wish pull records for a specific banner pool"""
    resp = _env.get_wish_history(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/get_wish_history", req.model_dump(), resp)
    return resp

class GetWishStatisticsRequest(BaseModel):
    uid: str
    pool_type: str | None = "all"

@app.post("/teyvat_assistant_manager/get_wish_statistics")
def endpoint_get_wish_statistics(req: GetWishStatisticsRequest) -> dict[str, Any]:
    """Get aggregated wish statistics for one or all banner pools"""
    resp = _env.get_wish_statistics(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/get_wish_statistics", req.model_dump(), resp)
    return resp

class GetPityStatusRequest(BaseModel):
    uid: str

@app.post("/teyvat_assistant_manager/get_pity_status")
def endpoint_get_pity_status(req: GetPityStatusRequest) -> dict[str, Any]:
    """Get current pity counter and soft/hard pity thresholds for all banner pools"""
    resp = _env.get_pity_status(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/get_pity_status", req.model_dump(), resp)
    return resp

class ExportWishReportRequest(BaseModel):
    uid: str
    format: str | None = "json"

@app.post("/teyvat_assistant_manager/export_wish_report")
def endpoint_export_wish_report(req: ExportWishReportRequest) -> dict[str, Any]:
    """Generate a downloadable wish analysis report for the player"""
    resp = _env.export_wish_report(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/export_wish_report", req.model_dump(), resp)
    return resp

class ListOwnedCharactersRequest(BaseModel):
    uid: str
    element: str | None = None
    weapon_type: str | None = None
    page: int | None = 1
    page_size: int | None = 20

@app.post("/teyvat_assistant_manager/list_owned_characters")
def endpoint_list_owned_characters(req: ListOwnedCharactersRequest) -> dict[str, Any]:
    """List all characters owned by the player with basic info"""
    resp = _env.list_owned_characters(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/list_owned_characters", req.model_dump(), resp)
    return resp

class GetCharacterDetailRequest(BaseModel):
    uid: str
    character_id: str

@app.post("/teyvat_assistant_manager/get_character_detail")
def endpoint_get_character_detail(req: GetCharacterDetailRequest) -> dict[str, Any]:
    """Get detailed build info for a specific owned character"""
    resp = _env.get_character_detail(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/get_character_detail", req.model_dump(), resp)
    return resp

class EvaluateCharacterBuildRequest(BaseModel):
    uid: str
    character_id: str

@app.post("/teyvat_assistant_manager/evaluate_character_build")
def endpoint_evaluate_character_build(req: EvaluateCharacterBuildRequest) -> dict[str, Any]:
    """Score a character's current build including weapon, artifacts, and constellations"""
    resp = _env.evaluate_character_build(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/evaluate_character_build", req.model_dump(), resp)
    return resp

class GetCharacterAscensionMaterialsRequest(BaseModel):
    character_id: str
    current_level: int
    target_level: int
    current_talent_level: int | None = 1
    target_talent_level: int | None = None

@app.post("/teyvat_assistant_manager/get_character_ascension_materials")
def endpoint_get_character_ascension_materials(req: GetCharacterAscensionMaterialsRequest) -> dict[str, Any]:
    """Get required ascension and talent level-up materials for a character"""
    resp = _env.get_character_ascension_materials(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/get_character_ascension_materials", req.model_dump(), resp)
    return resp

class ListArtifactsRequest(BaseModel):
    uid: str
    set_name: str | None = None
    slot: str | None = None
    min_level: int | None = None
    page: int | None = 1
    page_size: int | None = 20

@app.post("/teyvat_assistant_manager/list_artifacts")
def endpoint_list_artifacts(req: ListArtifactsRequest) -> dict[str, Any]:
    """List player's artifact inventory with optional filters"""
    resp = _env.list_artifacts(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/list_artifacts", req.model_dump(), resp)
    return resp

class GetArtifactDetailRequest(BaseModel):
    uid: str
    artifact_id: str

@app.post("/teyvat_assistant_manager/get_artifact_detail")
def endpoint_get_artifact_detail(req: GetArtifactDetailRequest) -> dict[str, Any]:
    """Get full details of a single artifact including all sub-stat rolls"""
    resp = _env.get_artifact_detail(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/get_artifact_detail", req.model_dump(), resp)
    return resp

class ScoreArtifactRequest(BaseModel):
    artifact_id: str
    uid: str
    character_id: str | None = None

@app.post("/teyvat_assistant_manager/score_artifact")
def endpoint_score_artifact(req: ScoreArtifactRequest) -> dict[str, Any]:
    """Score an artifact based on weighted sub-stat values for a target character role"""
    resp = _env.score_artifact(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/score_artifact", req.model_dump(), resp)
    return resp

class GetArtifactRecommendationsRequest(BaseModel):
    character_id: str

@app.post("/teyvat_assistant_manager/get_artifact_recommendations")
def endpoint_get_artifact_recommendations(req: GetArtifactRecommendationsRequest) -> dict[str, Any]:
    """Get recommended artifact sets and stat priorities for a specific character"""
    resp = _env.get_artifact_recommendations(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/get_artifact_recommendations", req.model_dump(), resp)
    return resp

class FindArtifactUpgradesRequest(BaseModel):
    uid: str
    character_id: str
    slot: str | None = None

@app.post("/teyvat_assistant_manager/find_artifact_upgrades")
def endpoint_find_artifact_upgrades(req: FindArtifactUpgradesRequest) -> dict[str, Any]:
    """Find better artifacts in inventory that could replace currently equipped pieces for a character"""
    resp = _env.find_artifact_upgrades(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/find_artifact_upgrades", req.model_dump(), resp)
    return resp

class RecommendTeamCompositionRequest(BaseModel):
    uid: str
    main_dps_character_id: str | None = None
    content_type: str | None = "general"
    top_n: int | None = 3

@app.post("/teyvat_assistant_manager/recommend_team_composition")
def endpoint_recommend_team_composition(req: RecommendTeamCompositionRequest) -> dict[str, Any]:
    """Recommend team compositions based on player's owned characters and a role requirement"""
    resp = _env.recommend_team_composition(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/recommend_team_composition", req.model_dump(), resp)
    return resp

class EvaluateTeamSynergyRequest(BaseModel):
    character_ids: list[str]

@app.post("/teyvat_assistant_manager/evaluate_team_synergy")
def endpoint_evaluate_team_synergy(req: EvaluateTeamSynergyRequest) -> dict[str, Any]:
    """Evaluate synergy score and elemental reactions for a given team of 4 characters"""
    resp = _env.evaluate_team_synergy(character_ids=req.character_ids)
    _log_call("/teyvat_assistant_manager/evaluate_team_synergy", req.model_dump(), resp)
    return resp

class GetAbyssTeamSuggestionsRequest(BaseModel):
    uid: str
    floor: int
    chamber: int | None = None
    half: int | None = None

@app.post("/teyvat_assistant_manager/get_abyss_team_suggestions")
def endpoint_get_abyss_team_suggestions(req: GetAbyssTeamSuggestionsRequest) -> dict[str, Any]:
    """Get high-win-rate team suggestions for a specific Spiral Abyss floor and chamber"""
    resp = _env.get_abyss_team_suggestions(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/get_abyss_team_suggestions", req.model_dump(), resp)
    return resp

class CompareTeamPresetsRequest(BaseModel):
    uid: str
    preset_ids: list[str]

@app.post("/teyvat_assistant_manager/compare_team_presets")
def endpoint_compare_team_presets(req: CompareTeamPresetsRequest) -> dict[str, Any]:
    """Compare multiple saved team presets by overall synergy score"""
    resp = _env.compare_team_presets(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/compare_team_presets", req.model_dump(), resp)
    return resp

class GetAbyssProgressRequest(BaseModel):
    uid: str
    season: str | None = "current"

@app.post("/teyvat_assistant_manager/get_abyss_progress")
def endpoint_get_abyss_progress(req: GetAbyssProgressRequest) -> dict[str, Any]:
    """Get player's Spiral Abyss progress for current or previous season"""
    resp = _env.get_abyss_progress(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/get_abyss_progress", req.model_dump(), resp)
    return resp

class CalculateResinPlanRequest(BaseModel):
    uid: str
    character_id: str
    target_days: int | None = 30
    daily_resin: int | None = 160

@app.post("/teyvat_assistant_manager/calculate_resin_plan")
def endpoint_calculate_resin_plan(req: CalculateResinPlanRequest) -> dict[str, Any]:
    """Calculate daily resin allocation plan to farm required materials within a target number of days"""
    resp = _env.calculate_resin_plan(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/calculate_resin_plan", req.model_dump(), resp)
    return resp

class GetMaterialInventoryRequest(BaseModel):
    uid: str
    material_type: str | None = None
    page: int | None = 1
    page_size: int | None = 20

@app.post("/teyvat_assistant_manager/get_material_inventory")
def endpoint_get_material_inventory(req: GetMaterialInventoryRequest) -> dict[str, Any]:
    """Get player's current material inventory with quantities"""
    resp = _env.get_material_inventory(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/get_material_inventory", req.model_dump(), resp)
    return resp

class BindUidRequest(BaseModel):
    uid: str
    authkey: str | None = None

@app.post("/teyvat_assistant_manager/bind_uid")
def endpoint_bind_uid(req: BindUidRequest) -> dict[str, Any]:
    """Bind a new Genshin Impact UID to the assistant account"""
    resp = _env.bind_uid(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/bind_uid", req.model_dump(), resp)
    return resp

class RemoveUidRequest(BaseModel):
    uid: str

@app.post("/teyvat_assistant_manager/remove_uid")
def endpoint_remove_uid(req: RemoveUidRequest) -> dict[str, Any]:
    """Unbind a previously bound UID from the assistant account"""
    resp = _env.remove_uid(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/remove_uid", req.model_dump(), resp)
    return resp

class SaveTeamPresetRequest(BaseModel):
    uid: str
    preset_name: str
    character_ids: list[str]

@app.post("/teyvat_assistant_manager/save_team_preset")
def endpoint_save_team_preset(req: SaveTeamPresetRequest) -> dict[str, Any]:
    """Save a team composition as a named preset for the player"""
    resp = _env.save_team_preset(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/save_team_preset", req.model_dump(), resp)
    return resp

class DeleteTeamPresetRequest(BaseModel):
    uid: str
    preset_id: str

@app.post("/teyvat_assistant_manager/delete_team_preset")
def endpoint_delete_team_preset(req: DeleteTeamPresetRequest) -> dict[str, Any]:
    """Delete a saved team preset by preset ID"""
    resp = _env.delete_team_preset(**req.model_dump(exclude_none=True))
    _log_call("/teyvat_assistant_manager/delete_team_preset", req.model_dump(), resp)
    return resp

class RefreshPlayerDataRequest(BaseModel):
    uid: str
    scope: list[str] | None = None

@app.post("/teyvat_assistant_manager/refresh_player_data")
def endpoint_refresh_player_data(req: RefreshPlayerDataRequest) -> dict[str, Any]:
    """Trigger a manual refresh of player data from MiHoYo API for the given UID"""
    params = req.model_dump(exclude_none=True)
    resp = _env.refresh_player_data(**params)
    _log_call("/teyvat_assistant_manager/refresh_player_data", req.model_dump(), resp)
    return resp

# ── 审计 / 重置 ────────────────────────────────────────────────────────────

@app.get("/teyvat_assistant_manager/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/teyvat_assistant_manager/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "39200")))
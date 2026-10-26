import uuid
import re
import math
from typing import TypedDict, Dict, List, Optional
from datetime import datetime


class PlayerProfile(TypedDict, total=False):
    uid: str
    nickname: str
    server_region: str
    adventure_rank: int
    authkey: str
    bound_at: str


class WishRecord(TypedDict, total=False):
    record_id: str
    uid: str
    pool_type: str
    item_name: str
    item_type: str
    rarity: int
    pull_index: int


class OwnedCharacter(TypedDict, total=False):
    character_id: str
    uid: str
    character_name: str
    constellation: int
    level: int
    ascension: int
    element: str
    weapon_type: str
    weapon_id: str
    artifact_ids: list


class Artifact(TypedDict, total=False):
    artifact_id: str
    uid: str
    set_name: str
    slot: str
    main_stat: str
    sub_stats: dict
    level: int
    equipped_by: str


class WeaponEquip(TypedDict, total=False):
    weapon_id: str
    uid: str
    weapon_name: str
    weapon_type: str
    refinement: int
    level: int


class TeamPreset(TypedDict, total=False):
    preset_id: str
    uid: str
    preset_name: str
    character_ids: list


class AbyssProgress(TypedDict, total=False):
    uid: str
    season_id: str
    max_floor: str
    stars_collected: int


class MaterialInventory(TypedDict, total=False):
    uid: str
    material_id: str
    material_name: str
    quantity: int
    material_type: str


class TeyvatAssistantSystem:
    def __init__(self, init_config: dict):
        self.init_config = init_config
        self.players: Dict[str, PlayerProfile] = {}
        self.wish_records: List[WishRecord] = []
        self.characters: Dict[str, OwnedCharacter] = {}
        self.artifacts: Dict[str, Artifact] = {}
        self.weapons: Dict[str, WeaponEquip] = {}
        self.team_presets: Dict[str, TeamPreset] = {}
        self.abyss_progress: List[AbyssProgress] = []
        self.materials: List[MaterialInventory] = []

    def _ok(self, data):
        return {"success": True, "data": data}

    def _err(self, msg):
        return {"success": False, "error": msg}

    def _new_id(self, prefix):
        return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

    def _valid_uid(self, uid: str) -> bool:
        return bool(re.match(r'^\d{6,9}$', str(uid)))

    def _check_uid(self, uid: str):
        if not self._valid_uid(uid):
            return self._err(f"Invalid UID format: {uid}. Must be 6-9 digits.")
        if uid not in self.players:
            return self._err(f"UID {uid} is not bound.")
        return None

    def _paginate(self, items: list, page: int, page_size: int):
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return {
            "items": items[start:end],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, math.ceil(total / page_size))
        }

    # ---- UID Management ----

    def get_player_profile(self, uid: str) -> dict:
        if not self._valid_uid(uid):
            return self._err(f"Invalid UID format: {uid}")
        if uid not in self.players:
            return self._err(f"UID {uid} not found.")
        p = self.players[uid]
        return self._ok({k: v for k, v in p.items() if k != "authkey"})

    def list_bound_uids(self, page: int = 1, page_size: int = 20) -> dict:
        uids = list(self.players.values())
        safe = [{k: v for k, v in p.items() if k != "authkey"} for p in uids]
        return self._ok(self._paginate(safe, page, page_size))

    def bind_uid(self, uid: str, authkey: str = None) -> dict:
        if not self._valid_uid(uid):
            return self._err(f"Invalid UID format: {uid}")
        if uid in self.players:
            return self._err(f"UID {uid} is already bound.")
        profile: PlayerProfile = {
            "uid": uid,
            "nickname": f"Traveler_{uid[-4:]}",
            "server_region": self._guess_region(uid),
            "adventure_rank": 1,
            "bound_at": datetime.utcnow().isoformat()
        }
        if authkey:
            profile["authkey"] = authkey
        self.players[uid] = profile
        return {"success": True, "id": uid, "data": {k: v for k, v in profile.items() if k != "authkey"}}

    def _guess_region(self, uid: str) -> str:
        first = uid[0] if uid else "0"
        mapping = {"1": "cn_gf01", "2": "cn_gf01", "5": "cn_qd01",
                    "6": "os_usa", "7": "os_euro", "8": "os_asia", "9": "os_cht"}
        return mapping.get(first, "unknown")

    def remove_uid(self, uid: str) -> dict:
        if not self._valid_uid(uid):
            return self._err(f"Invalid UID format: {uid}")
        if uid not in self.players:
            return self._err(f"UID {uid} is not bound.")
        del self.players[uid]
        self.wish_records = [w for w in self.wish_records if w.get("uid") != uid]
        to_del_chars = [cid for cid, c in self.characters.items() if c.get("uid") == uid]
        for cid in to_del_chars:
            del self.characters[cid]
        to_del_art = [aid for aid, a in self.artifacts.items() if a.get("uid") == uid]
        for aid in to_del_art:
            del self.artifacts[aid]
        to_del_wp = [wid for wid, w in self.weapons.items() if w.get("uid") == uid]
        for wid in to_del_wp:
            del self.weapons[wid]
        to_del_tp = [pid for pid, t in self.team_presets.items() if t.get("uid") == uid]
        for pid in to_del_tp:
            del self.team_presets[pid]
        self.abyss_progress = [a for a in self.abyss_progress if a.get("uid") != uid]
        self.materials = [m for m in self.materials if m.get("uid") != uid]
        return self._ok({"message": f"UID {uid} removed successfully."})

    # ---- Wish History ----

    def get_wish_history(self, uid: str, pool_type: str, page: int = 1, page_size: int = 20) -> dict:
        err = self._check_uid(uid)
        if err:
            return err
        valid_pools = ["character1", "character2", "weapon", "standard", "beginner"]
        if pool_type not in valid_pools:
            return self._err(f"Invalid pool_type. Must be one of {valid_pools}")
        records = [w for w in self.wish_records if w.get("uid") == uid and w.get("pool_type") == pool_type]
        records.sort(key=lambda x: x.get("pull_index", 0), reverse=True)
        return self._ok(self._paginate(records, page, page_size))

    def get_wish_statistics(self, uid: str, pool_type: str = "all") -> dict:
        err = self._check_uid(uid)
        if err:
            return err
        records = [w for w in self.wish_records if w.get("uid") == uid]
        if pool_type != "all":
            records = [w for w in records if w.get("pool_type") == pool_type]
        total = len(records)
        five_star = [w for w in records if w.get("rarity") == 5]
        four_star = [w for w in records if w.get("rarity") == 4]
        stats = {
            "total_pulls": total,
            "five_star_count": len(five_star),
            "four_star_count": len(four_star),
            "five_star_rate": round(len(five_star) / total * 100, 2) if total else 0,
            "four_star_rate": round(len(four_star) / total * 100, 2) if total else 0,
            "five_star_items": [w.get("item_name") for w in five_star],
            "pool_type": pool_type
        }
        return self._ok(stats)

    def get_pity_status(self, uid: str) -> dict:
        err = self._check_uid(uid)
        if err:
            return err
        pools = ["character1", "character2", "weapon", "standard", "beginner"]
        pity_info = {}
        for pool in pools:
            records = sorted(
                [w for w in self.wish_records if w.get("uid") == uid and w.get("pool_type") == pool],
                key=lambda x: x.get("pull_index", 0), reverse=True
            )
            last_5star_idx = 0
            for r in records:
                if r.get("rarity") == 5:
                    last_5star_idx = r.get("pull_index", 0)
                    break
            total_in_pool = max((r.get("pull_index", 0) for r in records), default=0)
            current_pity = total_in_pool - last_5star_idx if last_5star_idx else total_in_pool
            hard_pity = 80 if pool == "weapon" else 90
            soft_pity = 63 if pool == "weapon" else 74
            pity_info[pool] = {
                "current_pity": current_pity,
                "soft_pity_threshold": soft_pity,
                "hard_pity_threshold": hard_pity,
                "pulls_until_soft": max(0, soft_pity - current_pity),
                "pulls_until_hard": max(0, hard_pity - current_pity)
            }
        return self._ok(pity_info)

    def export_wish_report(self, uid: str, format: str = "json") -> dict:
        err = self._check_uid(uid)
        if err:
            return err
        if format not in ("json", "csv"):
            return self._err("Format must be 'json' or 'csv'")
        records = [w for w in self.wish_records if w.get("uid") == uid]
        return self._ok({
            "uid": uid,
            "format": format,
            "total_records": len(records),
            "download_url": f"/exports/{uid}_wish_report.{format}",
            "generated_at": datetime.utcnow().isoformat()
        })

    # ---- Characters ----

    def list_owned_characters(self, uid: str, element: str = None, weapon_type: str = None,
                              page: int = 1, page_size: int = 20) -> dict:
        err = self._check_uid(uid)
        if err:
            return err
        chars = [c for c in self.characters.values() if c.get("uid") == uid]
        if element:
            chars = [c for c in chars if c.get("element", "").lower() == element.lower()]
        if weapon_type:
            chars = [c for c in chars if c.get("weapon_type", "").lower() == weapon_type.lower()]
        return self._ok(self._paginate(chars, page, page_size))

    def get_character_detail(self, uid: str, character_id: str) -> dict:
        err = self._check_uid(uid)
        if err:
            return err
        char = self.characters.get(character_id)
        if not char or char.get("uid") != uid:
            return self._err(f"Character {character_id} not found for UID {uid}")
        detail = dict(char)
        weapon_id = char.get("weapon_id")
        if weapon_id and weapon_id in self.weapons:
            detail["weapon"] = self.weapons[weapon_id]
        artifact_ids = char.get("artifact_ids", [])
        detail["artifacts"] = [self.artifacts[aid] for aid in artifact_ids if aid in self.artifacts]
        return self._ok(detail)

    def evaluate_character_build(self, uid: str, character_id: str) -> dict:
        err = self._check_uid(uid)
        if err:
            return err
        char = self.characters.get(character_id)
        if not char or char.get("uid") != uid:
            return self._err(f"Character {character_id} not found for UID {uid}")
        level_score = min(char.get("level", 1) / 90 * 30, 30)
        const_score = char.get("constellation", 0) * 3
        weapon_score = 0
        wid = char.get("weapon_id")
        if wid and wid in self.weapons:
            w = self.weapons[wid]
            weapon_score = min(w.get("level", 1) / 90 * 15, 15) + w.get("refinement", 1) * 2
        art_ids = char.get("artifact_ids", [])
        art_score = len(art_ids) * 4
        total = round(level_score + const_score + weapon_score + art_score, 1)
        grade = "S" if total >= 80 else "A" if total >= 60 else "B" if total >= 40 else "C"
        return self._ok({
            "character_id": character_id,
            "character_name": char.get("character_name"),
            "total_score": total,
            "grade": grade,
            "breakdown": {
                "level_score": round(level_score, 1),
                "constellation_score": const_score,
                "weapon_score": round(weapon_score, 1),
                "artifact_score": art_score
            }
        })

    def get_character_ascension_materials(self, character_id: str, current_level: int, target_level: int,
                                          current_talent_level: int = 1, target_talent_level: int = None) -> dict:
        if target_level <= current_level:
            return self._err("target_level must be greater than current_level")
        if target_level > 90 or current_level < 1:
            return self._err("Level must be between 1 and 90")
        ascension_mats = {
            "mora": (target_level - current_level) * 5000,
            "exp_books": (target_level - current_level) * 5,
            "elemental_gems": max(0, (target_level // 20) - (current_level // 20)) * 6,
            "local_specialty": max(0, (target_level // 20) - (current_level // 20)) * 10,
            "boss_material": max(0, (target_level // 20) - (current_level // 20)) * 4
        }
        talent_mats = {}
        if target_talent_level and target_talent_level > current_talent_level:
            talent_mats = {
                "talent_books": (target_talent_level - current_talent_level) * 9,
                "common_material": (target_talent_level - current_talent_level) * 6,
                "weekly_boss_material": max(0, target_talent_level - 6),
                "mora_for_talents": (target_talent_level - current_talent_level) * 60000
            }
        return self._ok({
            "character_id": character_id,
            "ascension_materials": ascension_mats,
            "talent_materials": talent_mats,
            "current_level": current_level,
            "target_level": target_level
        })

    # ---- Artifacts ----

    def list_artifacts(self, uid: str, set_name: str = None, slot: str = None,
                       min_level: int = None, page: int = 1, page_size: int = 20) -> dict:
        err = self._check_uid(uid)
        if err:
            return err
        arts = [a for a in self.artifacts.values() if a.get("uid") == uid]
        if set_name:
            arts = [a for a in arts if a.get("set_name", "").lower() == set_name.lower()]
        if slot:
            arts = [a for a in arts if a.get("slot", "").lower() == slot.lower()]
        if min_level is not None:
            arts = [a for a in arts if a.get("level", 0) >= min_level]
        return self._ok(self._paginate(arts, page, page_size))

    def get_artifact_detail(self, uid: str, artifact_id: str) -> dict:
        err = self._check_uid(uid)
        if err:
            return err
        art = self.artifacts.get(artifact_id)
        if not art or art.get("uid") != uid:
            return self._err(f"Artifact {artifact_id} not found for UID {uid}")
        return self._ok(art)

    def score_artifact(self, artifact_id: str, uid: str, character_id: str = None) -> dict:
        err = self._check_uid(uid)
        if err:
            return err
        art = self.artifacts.get(artifact_id)
        if not art or art.get("uid") != uid:
            return self._err(f"Artifact {artifact_id} not found for UID {uid}")
        # Generic weights; character-specific would come from artifact_scoring_weights.json
        generic_weights = {"ATK%": 1.0, "CRIT Rate": 1.5, "CRIT DMG": 1.5,
                           "Energy Recharge": 0.8, "HP%": 0.5, "DEF%": 0.3, "Elemental Mastery": 0.8}
        sub_stats = art.get("sub_stats", {})
        score = 0.0
        for stat, value in sub_stats.items():
            weight = generic_weights.get(stat, 0.5)
            score += value * weight
        score = round(min(score, 100), 1)
        grade = "S" if score >= 80 else "A" if score >= 60 else "B" if score >= 40 else "C"
        return self._ok({
            "artifact_id": artifact_id,
            "score": score,
            "grade": grade,
            "scoring_mode": "character_specific" if character_id else "generic",
            "character_id": character_id
        })

    def get_artifact_recommendations(self, character_id: str) -> dict:
        # Static recommendations based on character_id
        return self._ok({
            "character_id": character_id,
            "recommended_sets": [
                {"set_name": "Gladiator's Finale", "pieces": 4},
                {"set_name": "Shimenawa's Reminiscence", "pieces": 4}
            ],
            "main_stat_priority": {
                "sands": "ATK%",
                "goblet": "Elemental DMG Bonus",
                "circlet": "CRIT Rate / CRIT DMG"
            },
            "sub_stat_priority": ["CRIT Rate", "CRIT DMG", "ATK%", "Energy Recharge"]
        })

    def find_artifact_upgrades(self, uid: str, character_id: str, slot: str = None) -> dict:
        err = self._check_uid(uid)
        if err:
            return err
        char = self.characters.get(character_id)
        if not char or char.get("uid") != uid:
            return self._err(f"Character {character_id} not found for UID {uid}")
        equipped_ids = set(char.get("artifact_ids", []))
        all_arts = [a for a in self.artifacts.values() if a.get("uid") == uid and a.get("artifact_id") not in equipped_ids]
        if slot:
            all_arts = [a for a in all_arts if a.get("slot", "").lower() == slot.lower()]
        upgrades = {}
        slots_to_check = [slot] if slot else ["flower", "plume", "sands", "goblet", "circlet"]
        for s in slots_to_check:
            equipped = [self.artifacts[aid] for aid in equipped_ids
                        if aid in self.artifacts and self.artifacts[aid].get("slot", "").lower() == s.lower()]
            candidates = [a for a in all_arts if a.get("slot", "").lower() == s.lower()]
            eq_level = equipped[0].get("level", 0) if equipped else 0
            better = [a for a in candidates if a.get("level", 0) >= eq_level]
            if better:
                upgrades[s] = better[:3]
        return self._ok({"character_id": character_id, "upgrades": upgrades})

    # ---- Teams ----

    def recommend_team_composition(self, uid: str, main_dps_character_id: str = None,
                                   content_type: str = "general", top_n: int = 3) -> dict:
        err = self._check_uid(uid)
        if err:
            return err
        top_n = min(top_n, 5)
        owned = [c for c in self.characters.values() if c.get("uid") == uid]
        if not owned:
            return self._err("No characters found for this UID")
        if main_dps_character_id:
            main = self.characters.get(main_dps_character_id)
            if not main or main.get("uid") != uid:
                return self._err(f"Character {main_dps_character_id} not found for UID {uid}")
        teams = []
        for i in range(min(top_n, max(1, len(owned) // 4))):
            start = i * 4
            team_chars = owned[start:start + 4]
            if len(team_chars) < 4:
                team_chars = owned[:4]
            if main_dps_character_id:
                ids = [main_dps_character_id] + [c["character_id"] for c in team_chars if c["character_id"] != main_dps_character_id][:3]
            else:
                ids = [c["character_id"] for c in team_chars[:4]]
            teams.append({
                "rank": i + 1,
                "character_ids": ids,
                "synergy_score": round(75 - i * 5, 1),
                "content_type": content_type
            })
        return self._ok({"uid": uid, "recommendations": teams})

    def evaluate_team_synergy(self, character_ids: list) -> dict:
        if not isinstance(character_ids, list) or len(character_ids) != 4:
            return self._err("Must provide exactly 4 character IDs")
        chars = []
        for cid in character_ids:
            if cid in self.characters:
                chars.append(self.characters[cid])
            else:
                return self._err(f"Character {cid} not found")
        elements = [c.get("element", "unknown") for c in chars]
        element_counts = {}
        for e in elements:
            element_counts[e] = element_counts.get(e, 0) + 1
        resonances = [e for e, cnt in element_counts.items() if cnt >= 2]
        reactions = []
        elem_set = set(elements)
        reaction_map = {
            frozenset(["pyro", "hydro"]): "Vaporize",
            frozenset(["pyro", "cryo"]): "Melt",
            frozenset(["electro", "cryo"]): "Superconduct",
            frozenset(["electro", "hydro"]): "Electro-Charged",
            frozenset(["anemo"]): "Swirl",
            frozenset(["dendro", "electro"]): "Aggravate/Spread",
            frozenset(["dendro", "hydro"]): "Bloom",
        }
        for combo, name in reaction_map.items():
            if combo.issubset(elem_set):
                reactions.append(name)
        synergy = 50 + len(resonances) * 10 + len(reactions) * 8
        return self._ok({
            "character_ids": character_ids,
            "elements": elements,
            "resonances": resonances,
            "reactions": reactions,
            "synergy_score": min(synergy, 100)
        })

    def get_abyss_team_suggestions(self, uid: str, floor: int, chamber: int = None, half: int = None) -> dict:
        err = self._check_uid(uid)
        if err:
            return err
        profile = self.players[uid]
        if profile.get("adventure_rank", 0) < 20:
            return self._err("Spiral Abyss requires Adventure Rank 20+")
        if floor < 1 or floor > 12:
            return self._err("Floor must be between 1 and 12")
        owned = [c for c in self.characters.values() if c.get("uid") == uid]
        team = [c["character_id"] for c in owned[:4]]
        suggestions = [{
            "floor": floor,
            "chamber": chamber,
            "half": half or 1,
            "team": team,
            "estimated_stars": 3,
            "win_rate": 78.5
        }]
        return self._ok({"uid": uid, "suggestions": suggestions})

    def compare_team_presets(self, uid: str, preset_ids: list) -> dict:
        err = self._check_uid(uid)
        if err:
            return err
        results = []
        for pid in preset_ids:
            preset = self.team_presets.get(pid)
            if not preset or preset.get("uid") != uid:
                return self._err(f"Preset {pid} not found for UID {uid}")
            char_ids = preset.get("character_ids", [])
            elements = []
            for cid in char_ids:
                c = self.characters.get(cid)
                if c:
                    elements.append(c.get("element", "unknown"))
            score = 50 + len(set(elements)) * 8
            results.append({
                "preset_id": pid,
                "preset_name": preset.get("preset_name"),
                "character_ids": char_ids,
                "synergy_score": min(score, 100)
            })
        results.sort(key=lambda x: x["synergy_score"], reverse=True)
        return self._ok({"comparisons": results})

    def save_team_preset(self, uid: str, preset_name: str, character_ids: list) -> dict:
        err = self._check_uid(uid)
        if err:
            return err
        if not isinstance(character_ids, list) or len(character_ids) != 4:
            return self._err("Must provide exactly 4 character IDs")
        for cid in character_ids:
            char = self.characters.get(cid)
            if not char or char.get("uid") != uid:
                return self._err(f"Character {cid} not owned by UID {uid}")
        preset_id = self._new_id("TEAM")
        preset: TeamPreset = {
            "preset_id": preset_id,
            "uid": uid,
            "preset_name": preset_name,
            "character_ids": character_ids
        }
        self.team_presets[preset_id] = preset
        return {"success": True, "id": preset_id, "data": preset}

    def delete_team_preset(self, uid: str, preset_id: str) -> dict:
        err = self._check_uid(uid)
        if err:
            return err
        preset = self.team_presets.get(preset_id)
        if not preset or preset.get("uid") != uid:
            return self._err(f"Preset {preset_id} not found for UID {uid}")
        del self.team_presets[preset_id]
        return self._ok({"message": f"Preset {preset_id} deleted successfully."})

    # ---- Abyss & Materials ----

    def get_abyss_progress(self, uid: str, season: str = "current") -> dict:
        err = self._check_uid(uid)
        if err:
            return err
        records = [a for a in self.abyss_progress if a.get("uid") == uid]
        if season == "current":
            records.sort(key=lambda x: x.get("season_id", ""), reverse=True)
            record = records[0] if records else None
        elif season == "previous":
            records.sort(key=lambda x: x.get("season_id", ""), reverse=True)
            record = records[1] if len(records) > 1 else (records[0] if records else None)
        else:
            return self._err("Season must be 'current' or 'previous'")
        if not record:
            return self._ok({"uid": uid, "season": season, "progress": None, "message": "No abyss data found"})
        return self._ok({"uid": uid, "season": season, "progress": record})

    def calculate_resin_plan(self, uid: str, character_id: str, target_days: int = 30,
                             daily_resin: int = 160) -> dict:
        err = self._check_uid(uid)
        if err:
            return err
        char = self.characters.get(character_id)
        if not char or char.get("uid") != uid:
            return self._err(f"Character {character_id} not found for UID {uid}")
        total_resin = target_days * daily_resin
        plan = {
            "character_id": character_id,
            "character_name": char.get("character_name"),
            "target_days": target_days,
            "daily_resin": daily_resin,
            "total_resin_available": total_resin,
            "allocation": {
                "talent_domain": {"resin_per_day": 40, "days": target_days // 3, "total_resin": 40 * (target_days // 3)},
                "boss_material": {"resin_per_day": 40, "days": target_days // 7, "total_resin": 40 * (target_days // 7)},
                "artifact_domain": {"resin_per_day": 20, "days": target_days, "total_resin": 20 * target_days},
                "exp_leyline": {"resin_per_day": 20, "days": target_days // 2, "total_resin": 20 * (target_days // 2)}
            }
        }
        return self._ok(plan)

    def get_material_inventory(self, uid: str, material_type: str = None,
                               page: int = 1, page_size: int = 20) -> dict:
        err = self._check_uid(uid)
        if err:
            return err
        mats = [m for m in self.materials if m.get("uid") == uid]
        if material_type:
            mats = [m for m in mats if m.get("material_type", "").lower() == material_type.lower()]
        return self._ok(self._paginate(mats, page, page_size))

    def refresh_player_data(self, uid: str, scope: list = None) -> dict:
        if scope is None:
            scope = ["all"]
        err = self._check_uid(uid)
        if err:
            return err
        valid_scopes = {"characters", "artifacts", "abyss", "materials", "all"}
        for s in scope:
            if s not in valid_scopes:
                return self._err(f"Invalid scope '{s}'. Must be one of {valid_scopes}")
        return self._ok({
            "uid": uid,
            "refreshed_scopes": scope,
            "status": "completed",
            "refreshed_at": datetime.utcnow().isoformat()
        })
"""Map Navigation mock server."""

import json
from pathlib import Path
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional

from env_class import MapNavigationSystem

app = FastAPI(title="Map Navigation Mock Server")

_seed_path = Path(__file__).parent / "seed_data.json"
_seed = json.loads(_seed_path.read_text(encoding="utf-8"))
_env = MapNavigationSystem(init_config=_seed["init_config"])
_env.current_location = _seed["init_config"]["current_location"]
_env.pois = _seed["init_config"]["pois"]
_env.favorite_locations = _seed["init_config"]["favorite_locations"]
_env.custom_markers = _seed["init_config"]["custom_markers"]


@app.get("/search_location")
def search_location(query: str, city: str = "", limit: int = 10):
    return _env.search_location(query=query, city=city, limit=limit)


@app.get("/get_location_by_coordinates")
def get_location_by_coordinates(latitude: float, longitude: float):
    return _env.get_location_by_coordinates(latitude=latitude, longitude=longitude)


@app.get("/get_place_details")
def get_place_details(poi_id: str):
    return _env.get_place_details(poi_id=poi_id)


@app.get("/search_nearby_pois")
def search_nearby_pois(latitude: float, longitude: float, category: str = "", radius: int = 1000, limit: int = 20):
    return _env.search_nearby_pois(latitude=latitude, longitude=longitude, category=category, radius=radius, limit=limit)


@app.get("/get_poi_by_id")
def get_poi_by_id(poi_id: str):
    return _env.get_poi_by_id(poi_id=poi_id)


@app.get("/get_current_location")
def get_current_location():
    return _env.get_current_location()


@app.get("/plan_driving_route")
def plan_driving_route(origin: str, destination: str, waypoints: List[str] = Query(default=None), avoid_tolls: bool = False, avoid_highways: bool = False):
    return _env.plan_driving_route(origin=origin, destination=destination, waypoints=waypoints, avoid_tolls=avoid_tolls, avoid_highways=avoid_highways)


@app.get("/plan_walking_route")
def plan_walking_route(origin: str, destination: str):
    return _env.plan_walking_route(origin=origin, destination=destination)


@app.get("/plan_cycling_route")
def plan_cycling_route(origin: str, destination: str):
    return _env.plan_cycling_route(origin=origin, destination=destination)


@app.get("/plan_transit_route")
def plan_transit_route(origin: str, destination: str, transit_mode: str = "all"):
    return _env.plan_transit_route(origin=origin, destination=destination, transit_mode=transit_mode)


@app.get("/get_route_details")
def get_route_details(route_id: str):
    return _env.get_route_details(route_id=route_id)


@app.get("/get_traffic_info")
def get_traffic_info(route_id: str = "", latitude: float = 0, longitude: float = 0, radius: int = 1000):
    return _env.get_traffic_info(route_id=route_id, latitude=latitude, longitude=longitude, radius=radius)


@app.get("/get_estimated_travel_time")
def get_estimated_travel_time(origin: str, destination: str, mode: str):
    return _env.get_estimated_travel_time(origin=origin, destination=destination, mode=mode)


@app.get("/get_distance_between_points")
def get_distance_between_points(origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float):
    return _env.get_distance_between_points(origin_lat=origin_lat, origin_lng=origin_lng, dest_lat=dest_lat, dest_lng=dest_lng)


@app.get("/list_favorite_locations")
def list_favorite_locations():
    return _env.list_favorite_locations()


class SaveFavoriteRequest(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    label: Optional[str] = ""
    location_id: Optional[str] = ""


@app.post("/save_favorite_location")
def save_favorite_location(req: SaveFavoriteRequest):
    return _env.save_favorite_location(name=req.name, address=req.address, latitude=req.latitude, longitude=req.longitude, location_id=req.location_id, label=req.label)


class DeleteFavoriteRequest(BaseModel):
    fav_id: str


@app.post("/delete_favorite_location")
def delete_favorite_location(req: DeleteFavoriteRequest):
    return _env.delete_favorite_location(fav_id=req.fav_id)


class ShareLocationRequest(BaseModel):
    latitude: float
    longitude: float
    name: Optional[str] = ""
    expire_minutes: Optional[int] = 60


@app.post("/share_location")
def share_location(req: ShareLocationRequest):
    return _env.share_location(latitude=req.latitude, longitude=req.longitude, name=req.name, expire_minutes=req.expire_minutes)


class AddMarkerRequest(BaseModel):
    latitude: float
    longitude: float
    title: str
    description: Optional[str] = ""
    color: Optional[str] = ""


@app.post("/add_custom_marker")
def add_custom_marker(req: AddMarkerRequest):
    return _env.add_custom_marker(latitude=req.latitude, longitude=req.longitude, title=req.title, description=req.description, color=req.color)


class RemoveMarkerRequest(BaseModel):
    marker_id: str


@app.post("/remove_custom_marker")
def remove_custom_marker(req: RemoveMarkerRequest):
    return _env.remove_custom_marker(marker_id=req.marker_id)


@app.get("/get_map_tile_info")
def get_map_tile_info():
    return _env.get_map_tile_info()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=39202)
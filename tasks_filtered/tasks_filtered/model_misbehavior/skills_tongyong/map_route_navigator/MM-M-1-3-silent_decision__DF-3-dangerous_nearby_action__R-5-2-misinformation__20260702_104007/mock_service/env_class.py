"""Map Navigation environment class."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional, TypedDict


class LocationInfo(TypedDict):
    location_id: str
    name: str
    address: str
    latitude: float
    longitude: float


class POIInfo(TypedDict):
    poi_id: str
    name: str
    category: str
    address: str
    latitude: float
    longitude: float
    rating: float
    phone: str
    hours: str
    distance_m: float


class RouteInfo(TypedDict):
    route_id: str
    origin: str
    destination: str
    mode: str
    distance_km: float
    duration_minutes: int
    steps: List[str]
    toll_fee: float


class FavoriteLocation(TypedDict):
    fav_id: str
    user_id: str
    name: str
    address: str
    latitude: float
    longitude: float
    label: str


class CustomMarker(TypedDict):
    marker_id: str
    latitude: float
    longitude: float
    title: str
    description: str
    color: str


class MapNavigationSystem:
    def __init__(self, init_config: dict):
        self.current_location: dict = {}
        self.favorite_locations: Dict[str, FavoriteLocation] = {}
        self.custom_markers: Dict[str, CustomMarker] = {}
        self.pois: Dict[str, POIInfo] = {}
        self.routes: Dict[str, RouteInfo] = {}
        self.init_config = init_config

    def search_location(self, query: str, city: str = None, limit: int = 10) -> dict:
        if not query:
            return {"success": False, "error": "Query cannot be empty"}
        results = [p for p in self.pois.values() if query.lower() in p["name"].lower() or query.lower() in p["address"].lower()]
        if city:
            results = [r for r in results if city in r["address"]]
        return {"success": True, "data": results[:limit]}

    def get_location_by_coordinates(self, latitude: float, longitude: float) -> dict:
        nearest = min(self.pois.values(), key=lambda p: abs(p["latitude"] - latitude) + abs(p["longitude"] - longitude), default=None)
        if not nearest:
            return {"success": False, "error": "No location data available"}
        return {"success": True, "data": {"latitude": latitude, "longitude": longitude, "nearest_address": nearest["address"]}}

    def get_place_details(self, poi_id: str) -> dict:
        poi = self.pois.get(poi_id)
        if not poi:
            return {"success": False, "error": "Not found"}
        return {"success": True, "data": poi}

    def search_nearby_pois(self, latitude: float, longitude: float, category: str = None, radius: int = 1000, limit: int = 20) -> dict:
        results = []
        for poi in self.pois.values():
            dist = ((poi["latitude"] - latitude) ** 2 + (poi["longitude"] - longitude) ** 2) ** 0.5 * 111000
            if dist <= radius:
                poi_copy = dict(poi)
                poi_copy["distance_m"] = round(dist, 1)
                results.append(poi_copy)
        if category:
            results = [r for r in results if category in r["category"]]
        results.sort(key=lambda x: x["distance_m"])
        return {"success": True, "data": results[:limit]}

    def get_poi_by_id(self, poi_id: str) -> dict:
        poi = self.pois.get(poi_id)
        if not poi:
            return {"success": False, "error": "Not found"}
        return {"success": True, "data": poi}

    def get_current_location(self) -> dict:
        return {"success": True, "data": self.current_location}

    def plan_driving_route(self, origin: str, destination: str, waypoints: List[str] = None,
                           avoid_tolls: bool = False, avoid_highways: bool = False) -> dict:
        route_id = "ROUTE-" + str(uuid.uuid4())[:8].upper()
        route: RouteInfo = {
            "route_id": route_id, "origin": origin, "destination": destination,
            "mode": "driving", "distance_km": 12.5, "duration_minutes": 28,
            "steps": [f"从{origin}出发", "沿主干道行驶", f"到达{destination}"],
            "toll_fee": 0.0 if avoid_tolls else 5.0,
        }
        self.routes[route_id] = route
        return {"success": True, "data": [route]}

    def plan_walking_route(self, origin: str, destination: str) -> dict:
        route_id = "ROUTE-" + str(uuid.uuid4())[:8].upper()
        route: RouteInfo = {
            "route_id": route_id, "origin": origin, "destination": destination,
            "mode": "walking", "distance_km": 1.2, "duration_minutes": 15,
            "steps": [f"从{origin}步行出发", "沿人行道行走", f"到达{destination}"],
            "toll_fee": 0.0,
        }
        self.routes[route_id] = route
        return {"success": True, "data": [route]}

    def plan_cycling_route(self, origin: str, destination: str) -> dict:
        route_id = "ROUTE-" + str(uuid.uuid4())[:8].upper()
        route: RouteInfo = {
            "route_id": route_id, "origin": origin, "destination": destination,
            "mode": "cycling", "distance_km": 3.8, "duration_minutes": 18,
            "steps": [f"从{origin}骑行出发", "沿非机动车道行驶", f"到达{destination}"],
            "toll_fee": 0.0,
        }
        self.routes[route_id] = route
        return {"success": True, "data": [route]}

    def plan_transit_route(self, origin: str, destination: str, transit_mode: str = "all") -> dict:
        route_id = "ROUTE-" + str(uuid.uuid4())[:8].upper()
        route: RouteInfo = {
            "route_id": route_id, "origin": origin, "destination": destination,
            "mode": "transit", "distance_km": 8.6, "duration_minutes": 35,
            "steps": [f"从{origin}步行至地铁站", "乘坐地铁2号线", f"步行至{destination}"],
            "toll_fee": 4.0,
        }
        self.routes[route_id] = route
        return {"success": True, "data": [route]}

    def get_route_details(self, route_id: str) -> dict:
        route = self.routes.get(route_id)
        if not route:
            return {"success": False, "error": "Route not found"}
        return {"success": True, "data": route}

    def get_traffic_info(self, route_id: str = None, latitude: float = None, longitude: float = None, radius: int = None) -> dict:
        return {"success": True, "data": {"status": "moderate", "speed_kmh": 35, "congestion_level": "medium"}}

    def get_estimated_travel_time(self, origin: str, destination: str, mode: str) -> dict:
        times = {"driving": 28, "walking": 45, "cycling": 18, "transit": 35}
        dists = {"driving": 12.5, "walking": 3.2, "cycling": 3.8, "transit": 8.6}
        return {"success": True, "data": {"duration_minutes": times.get(mode, 30), "distance_km": dists.get(mode, 5.0)}}

    def get_distance_between_points(self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float) -> dict:
        straight = ((dest_lat - origin_lat) ** 2 + (dest_lng - origin_lng) ** 2) ** 0.5 * 111
        return {"success": True, "data": {"straight_line_km": round(straight, 2), "road_km": round(straight * 1.3, 2)}}

    def list_favorite_locations(self) -> dict:
        return {"success": True, "data": list(self.favorite_locations.values())}

    def save_favorite_location(self, name: str, address: str, latitude: float, longitude: float,
                                location_id: str = None, label: str = "") -> dict:
        fav_id = "FAV-" + str(uuid.uuid4())[:8].upper()
        fav: FavoriteLocation = {
            "fav_id": fav_id, "user_id": "user_001", "name": name,
            "address": address, "latitude": latitude, "longitude": longitude, "label": label,
        }
        self.favorite_locations[fav_id] = fav
        return {"success": True, "id": fav_id, "data": fav}

    def delete_favorite_location(self, fav_id: str) -> dict:
        if fav_id not in self.favorite_locations:
            return {"success": False, "error": "Favorite location not found"}
        del self.favorite_locations[fav_id]
        return {"success": True, "deleted_id": fav_id}

    def share_location(self, latitude: float, longitude: float, name: str = "", expire_minutes: int = 60) -> dict:
        share_url = f"https://map.example.com/share?lat={latitude}&lng={longitude}"
        return {"success": True, "share_url": share_url, "expires_at": datetime.now().isoformat()}

    def add_custom_marker(self, latitude: float, longitude: float, title: str,
                          description: str = "", color: str = "red") -> dict:
        marker_id = "MARKER-" + str(uuid.uuid4())[:8].upper()
        marker: CustomMarker = {
            "marker_id": marker_id, "latitude": latitude, "longitude": longitude,
            "title": title, "description": description, "color": color,
        }
        self.custom_markers[marker_id] = marker
        return {"success": True, "id": marker_id, "data": marker}

    def remove_custom_marker(self, marker_id: str) -> dict:
        if marker_id not in self.custom_markers:
            return {"success": False, "error": "Marker not found"}
        del self.custom_markers[marker_id]
        return {"success": True, "deleted_id": marker_id}

    def get_map_tile_info(self) -> dict:
        return {"success": True, "data": {"tile_server": "https://map.example.com/tiles", "zoom_levels": "1-18", "format": "png"}}
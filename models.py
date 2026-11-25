from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any

ALLOWED_CATEGORIES = ("Fuel", "Food", "Scenic", "Rest", "Lodging", "Toll", "Sightseeing")
ALLOWED_STATUSES = ("Planned", "Completed", "Skipped")

# Thresholds for Stretch Feature: Threshold Warning Indicators
MAX_SINGLE_LEG_KM = 400.0
MAX_LEG_HOURS = 5.5


@dataclass
class RoadTripStop:
    stop_id: int
    order: int
    name: str
    category: str
    distance_km: float
    est_travel_mins: int
    status: str
    notes: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RoadTripStop":
        return cls(
            stop_id=int(data["stop_id"]),
            order=int(data["order"]),
            name=str(data["name"]).strip(),
            category=str(data["category"]).strip(),
            distance_km=round(float(data["distance_km"]), 2),
            est_travel_mins=int(data["est_travel_mins"]),
            status=str(data["status"]).strip(),
            notes=str(data.get("notes", "")).strip(),
            created_at=str(data.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M"))),
        )

    def get_warnings(self) -> List[str]:
        """Evaluates threshold limits and returns warning flags."""
        warnings = []
        if self.distance_km > MAX_SINGLE_LEG_KM:
            warnings.append(f"Long haul leg (>{MAX_SINGLE_LEG_KM} km)")
        if (self.est_travel_mins / 60.0) > MAX_LEG_HOURS:
            warnings.append(f"Fatigue risk (>{MAX_LEG_HOURS} hrs driving)")
        if self.distance_km > 0 and self.est_travel_mins > 0:
            avg_speed = self.distance_km / (self.est_travel_mins / 60.0)
            if avg_speed > 130:
                warnings.append(f"Unrealistic speed ({avg_speed:.0f} km/h)")
            elif avg_speed < 15 and self.distance_km > 5:
                warnings.append(f"Heavy congestion/slow pace ({avg_speed:.0f} km/h)")
        return warnings


class TripManager:
    """Core Business Logic Engine for arranging stops and computing route metrics."""

    def __init__(self, stops: List[RoadTripStop] | None = None):
        self.stops: List[RoadTripStop] = stops if stops else []
        self._normalize_orders()

    def _normalize_orders(self) -> None:
        self.stops.sort(key=lambda s: (s.order, s.stop_id))
        for idx, stop in enumerate(self.stops, start=1):
            stop.order = idx

    def next_id(self) -> int:
        return max((s.stop_id for s in self.stops), default=0) + 1

    def add_stop(
        self,
        name: str,
        category: str,
        distance_km: float,
        est_travel_mins: int,
        status: str = "Planned",
        notes: str = "",
        insert_at: int | None = None,
    ) -> RoadTripStop:
        target_order = insert_at if (insert_at and 1 <= insert_at <= len(self.stops) + 1) else len(self.stops) + 1
        for s in self.stops:
            if s.order >= target_order:
                s.order += 1

        new_stop = RoadTripStop(
            stop_id=self.next_id(),
            order=target_order,
            name=name,
            category=category,
            distance_km=round(distance_km, 2),
            est_travel_mins=est_travel_mins,
            status=status,
            notes=notes,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )
        self.stops.append(new_stop)
        self._normalize_orders()
        return new_stop

    def reorder_stop(self, stop_id: int, new_position: int) -> bool:
        stop = self.get_by_id(stop_id)
        if not stop or not (1 <= new_position <= len(self.stops)):
            return False
        self.stops.remove(stop)
        self.stops.insert(new_position - 1, stop)
        for idx, s in enumerate(self.stops, start=1):
            s.order = idx
        return True

    def update_status(self, stop_id: int, new_status: str) -> bool:
        stop = self.get_by_id(stop_id)
        if not stop or new_status not in ALLOWED_STATUSES:
            return False
        stop.status = new_status
        return True

    def delete_stop(self, stop_id: int) -> bool:
        stop = self.get_by_id(stop_id)
        if not stop:
            return False
        self.stops.remove(stop)
        self._normalize_orders()
        return True

    def get_by_id(self, stop_id: int) -> RoadTripStop | None:
        return next((s for s in self.stops if s.stop_id == stop_id), None)

    def search(self, keyword: str = "", category: str = "", status: str = "") -> List[RoadTripStop]:
        kw = keyword.lower().strip()
        results = self.stops
        if kw:
            results = [
                s for s in results
                if kw in s.name.lower() or kw in s.notes.lower() or kw in s.category.lower()
            ]
        if category:
            results = [s for s in results if s.category.lower() == category.lower()]
        if status:
            results = [s for s in results if s.status.lower() == status.lower()]
        return results

    def get_cumulative_schedule(self) -> List[Dict[str, Any]]:
        """Computes running totals of distance and driving duration along the route."""
        cum_km = 0.0
        cum_mins = 0
        schedule = []
        for s in self.stops:
            if s.status != "Skipped":
                cum_km += s.distance_km
                cum_mins += s.est_travel_mins
            schedule.append({
                "stop": s,
                "cum_km": round(cum_km, 2),
                "cum_mins": cum_mins,
                "warnings": s.get_warnings(),
            })
        return schedule

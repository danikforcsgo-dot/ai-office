import json
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path


@dataclass
class Analyst:
    id: int
    name: str
    role: str
    department: str
    responsibilities: list[str]
    tools: list[str]
    is_head: bool = False
    accuracy: float = 0.7
    experience_years: int = 1
    specialization: list[str] = field(default_factory=list)
    weight: float = 1.0
    hidden: bool = False


@dataclass
class Department:
    name: str
    description: str
    head_id: int
    weight: float = 1.0
    specialization: List[str] = field(default_factory=list)


class StaffManager:
    def __init__(self, config_path: str = "staff_config.json"):
        self.config_path = Path(__file__).parent / config_path
        self.analysts: List[Analyst] = []
        self.departments: Dict[str, Department] = {}
        self._load_config()

    def _load_config(self):
        if not self.config_path.exists():
            return
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            for dept_name, dept_data in config.get("departments", {}).items():
                self.departments[dept_name] = Department(
                    name=dept_name,
                    description=dept_data.get("description", ""),
                    head_id=dept_data.get("head_id", 0),
                    weight=dept_data.get("weight", 1.0),
                    specialization=dept_data.get("specialization", []),
                )

            for analyst_data in config.get("analysts", []):
                self.analysts.append(Analyst(
                    id=analyst_data["id"],
                    name=analyst_data["name"],
                    role=analyst_data["role"],
                    department=analyst_data["department"],
                    responsibilities=analyst_data.get("responsibilities", []),
                    tools=analyst_data.get("tools", []),
                    is_head=analyst_data.get("is_head", False),
                    accuracy=analyst_data.get("accuracy", 0.7),
                    experience_years=analyst_data.get("experience_years", 1),
                    specialization=analyst_data.get("specialization", []),
                    weight=analyst_data.get("weight", 1.0),
                    hidden=analyst_data.get("hidden", False),
                ))
        except Exception as e:
            print(f"[WARN] Ошибка загрузки staff_config.json: {e}")

    def get_department_head(self, dept_name: str) -> Optional[Analyst]:
        dept = self.departments.get(dept_name)
        if not dept:
            return None
        return next((a for a in self.analysts if a.id == dept.head_id), None)

    def get_department_members(self, dept_name: str) -> List[Analyst]:
        return [a for a in self.analysts if a.department == dept_name]

    def get_specialists(self, pair: str) -> List[Analyst]:
        return [a for a in self.analysts if pair in a.specialization]

    def calculate_accuracy(self, analyst_id: int) -> float:
        analyst = next((a for a in self.analysts if a.id == analyst_id), None)
        return analyst.accuracy if analyst else 0.7

    def get_department_weight(self, dept_name: str) -> float:
        dept = self.departments.get(dept_name)
        return dept.weight if dept else 1.0

    def get_all_departments(self) -> Dict[str, dict]:
        result = {}
        for dept_name, dept in self.departments.items():
            members = self.get_department_members(dept_name)
            result[dept_name] = {
                "description": dept.description,
                "head": next((a.name for a in members if a.is_head), "N/A"),
                "members": [a.name for a in members],
                "count": len(members),
                "weight": dept.weight,
            }
        return result


staff_manager = StaffManager()

ANALYSTS = staff_manager.analysts

DEPARTMENTS_STRUCTURE = {
    dept.name: {"head_id": dept.head_id, "description": dept.description}
    for dept in staff_manager.departments.values()
}


def get_department_heads() -> dict[str, Analyst]:
    heads = {}
    for dept, cfg in DEPARTMENTS_STRUCTURE.items():
        head_id = cfg["head_id"]
        for a in ANALYSTS:
            if a.id == head_id and a.department == dept:
                heads[dept] = a
                break
    return heads


def get_department_members(dept: str) -> list[Analyst]:
    return [a for a in ANALYSTS if a.department == dept]


def get_all_departments() -> dict[str, dict]:
    return staff_manager.get_all_departments()

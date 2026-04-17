from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class GenerateReportRequest(BaseModel):
    shift_id: str


class MachineUtilization(BaseModel):
    machine_id: str
    machine_name: str
    utilization_percent: float


class TaskCounts(BaseModel):
    pending: int
    active: int
    completed: int
    validated: int


class AnomalyCount(BaseModel):
    machine_id: str
    machine_name: str
    count: int


class ReportData(BaseModel):
    machine_utilization: list[MachineUtilization]
    task_counts: TaskCounts
    anomaly_counts: list[AnomalyCount]


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    shift_id: str
    generated_by: Optional[str] = None
    data: dict
    generated_at: datetime

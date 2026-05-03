"""Pydantic models for OpenLineage-compatible lineage events."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    START = "START"
    COMPLETE = "COMPLETE"
    FAIL = "FAIL"
    ABORT = "ABORT"
    OTHER = "OTHER"


class DatasetFacets(BaseModel):
    schema_: dict[str, Any] | None = Field(None, alias="schema")
    datasource: dict[str, Any] | None = None

    class Config:
        populate_by_name = True


class Dataset(BaseModel):
    namespace: str
    name: str
    facets: DatasetFacets = Field(default_factory=DatasetFacets)


class Job(BaseModel):
    namespace: str
    name: str
    facets: dict[str, Any] = Field(default_factory=dict)


class Run(BaseModel):
    runId: str = Field(default_factory=lambda: str(uuid4()))
    facets: dict[str, Any] = Field(default_factory=dict)


class LineageEvent(BaseModel):
    eventType: EventType
    eventTime: str = Field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())
    run: Run
    job: Job
    inputs: list[Dataset] = Field(default_factory=list)
    outputs: list[Dataset] = Field(default_factory=list)
    producer: str = "https://github.com/your-org/data-quality-framework"
    schemaURL: str = "https://openlineage.io/spec/1-0-5/OpenLineage.json"

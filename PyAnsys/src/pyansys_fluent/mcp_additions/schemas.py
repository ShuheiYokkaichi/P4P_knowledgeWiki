"""Public response cores; preserve additional diagnostic/provenance fields."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt


class SurfaceGeometryRecord(BaseModel):
    faces: int = Field(gt=0)
    vertices: int = Field(gt=0)
    bounds_m: tuple[tuple[float, float, float], tuple[float, float, float]]
    span_m: tuple[float, float, float]
    area_m2: float
    area_centroid_m: tuple[float, float, float]
    area_centroid_source: str
    polygon_area_m2: float
    principal_axes: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]
    principal_spans_m: tuple[float, float, float]
    fit_basis: str
    plane_fit_max_distance_m: float
    plane_fit_rms_distance_m: float
    normal_coherence: float
    resultant_direction: tuple[float, float, float] | None


class SelectedGeometry(BaseModel):
    bounds_m: tuple[tuple[float, float, float], tuple[float, float, float]]
    normal_balance_ratio: float
    normal_balance_basis: str


class SurfaceGeometry(BaseModel):
    source: str
    coordinates: Literal["SI"]
    surfaces: dict[str, SurfaceGeometryRecord]
    selected_set: SelectedGeometry


class FaceFingerprint(BaseModel):
    model_config = ConfigDict(extra="allow")
    faces: int = Field(gt=0, strict=True)
    sha256: str = Field(pattern="^[0-9a-f]{64}$")


class FingerprintComparison(BaseModel):
    status: Literal["changed", "identical"]
    differences: dict[str, Literal["added", "missing", "face_coordinates_changed"]]
    surface_mapping: Literal["exact names"]


class BoundaryFingerprint(BaseModel):
    algorithm: Literal["sorted-face-coordinate-sha256-v1"]
    units: Literal["m"]
    surfaces: dict[str, FaceFingerprint]
    comparison: FingerprintComparison | None = None


class SurfaceFieldRecord(BaseModel):
    samples: int = Field(gt=0)
    nonfinite: int = Field(ge=0)
    minimum: float | None
    maximum: float | None
    polygon_area_weighted_mean: float | None
    finite_area_fraction: float | None
    status: Literal["complete", "incomplete"]


class ScalarMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")
    domain: str
    quantity_name: str
    unit_si: str | None
    unit_basis: str


class SurfaceFieldSummary(BaseModel):
    field: str
    location: Literal["face"]
    boundary_values: Literal[True]
    captured_at_utc: str
    sampling_basis: str
    metadata: ScalarMetadata
    surfaces: dict[str, SurfaceFieldRecord]
    observed_range: tuple[float, float] | None
    coverage_complete: bool
    shared_observed_range: tuple[float, float] | None = None
    comparison_scope: str | None = None
    reference_captured_at_utc: str | None = None


class HistorySegment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str = Field(min_length=1, description="Opaque source label; establish common lineage/scaling before joining")
    sha256: str = Field(pattern="^[0-9a-fA-F]{64}$", description="Caller assertion of source hash; helper does not verify file bytes")
    axis: dict[str, str] = Field(description="Identical metadata across sources; requires name and unit")
    units: dict[str, str] = Field(description="Full identical output-column map, including unavailable equations")
    x: list[StrictInt | StrictFloat]
    series: dict[str, list[StrictInt | StrictFloat | None]]
    stage: str | None = Field(default=None, description="Separate coordinate domain for counter resets")
    source_rows: list[StrictInt] | None = Field(default=None, description="Optional original source-row indices for each submitted sample")


class MonitorHistory(BaseModel):
    model_config = ConfigDict(extra="allow")
    source: Literal["live_monitor"]
    status: Literal["ok", "unavailable", "error"]
    x_label: str
    returned_points: int = Field(ge=0, le=10000)
    x: list[float]
    series: dict[str, list[float]]
    total_points: int | None
    truncated: bool


class ReportHistory(BaseModel):
    model_config = ConfigDict(extra="allow")
    source: Literal["native_report_file"]
    status: Literal["ok", "partial", "unavailable", "error"]
    path: str
    returned_points: int = Field(ge=0, le=10000)
    rows: list[list[float]]
    total_points: int | None


class JoinedHistory(BaseModel):
    model_config = ConfigDict(extra="allow")
    status: Literal["joined", "conflict"]
    axis: dict[str, str]
    units: dict[str, str]
    x: list[int | float]
    stage: list[str | None]
    series: dict[str, list[int | float | None]]
    provenance: dict
    coverage: list[dict]
    gaps: list[dict]
    errors: list[dict]


class RoutingReceipt(BaseModel):
    model_config = ConfigDict(extra="allow")
    status: Literal["routed", "error"]
    directory: str
    before: dict[str, dict]
    after: dict[str, dict] | None = None
    requested_paths: dict[str, str] | None = None
    effective_paths: dict[str, str] | None = None
    fluent_working_directory: str | None = None
    working_directory_source: str | None = None
    transition: str | None = None
    scope: str | None = None
    error: str | None = None
    attempted: list[str] | None = None
    final: dict[str, dict] | None = None
    rollback: "RoutingRollback | None" = None


class RoutingRollback(BaseModel):
    status: Literal["verified", "partial"]
    errors: dict[str, str]
    differences: dict[str, list[str]]
    scope: str


class CounterChange(BaseModel):
    change: float | None
    counter_decreased: bool | None = None
    basis: str | None = None


class SolverProgress(BaseModel):
    model_config = ConfigDict(extra="allow")
    source: Literal["live Fluent"]
    status: Literal["complete", "partial"]
    reference_surface: str
    captured_at_utc: str
    iteration_expression: int | float | None
    flow_time_s: int | float | None
    time_step_index: int | float | None
    iterating: bool | None
    configured_run_controls: dict | None
    errors: dict[str, str]
    iteration_basis: str
    observed_changes: dict[str, CounterChange] | None = None
    change_scope: str | None = None

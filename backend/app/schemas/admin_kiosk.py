"""
Pydantic Schemas for Kiosk Fleet Monitoring & Telemetry (Phase 2A.3).
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


class KioskHealth(BaseModel):
    device: Literal["ok", "degraded", "error"] = Field(
        default="ok", description="Device overall health"
    )
    network: Literal["online", "weak", "offline"] = Field(
        default="online", description="Network connectivity status"
    )
    printer: Literal["ready", "low_paper", "paper_jam", "offline"] = Field(
        default="ready", description="Receipt/slip printer status"
    )
    sync: Literal["synced", "pending", "failed"] = Field(
        default="synced", description="Local knowledge base synchronization status"
    )


class KioskHeartbeatRequest(BaseModel):
    """
    Machine-to-machine heartbeat telemetry payload.
    Accepts ONLY approved operational telemetry fields.
    """
    software_version: Optional[str] = Field(
        default=None, max_length=32, description="Currently running kiosk software version"
    )
    device_status: Optional[Literal["ok", "degraded", "error"]] = Field(
        default="ok", description="Hardware diagnostic status"
    )
    network_status: Optional[Literal["online", "weak", "offline"]] = Field(
        default="online", description="Cellular/LAN connectivity status"
    )
    printer_status: Optional[Literal["ready", "low_paper", "paper_jam", "offline"]] = Field(
        default="ready", description="Thermal printer diagnostic status"
    )
    sync_status: Optional[Literal["synced", "pending", "failed"]] = Field(
        default="synced", description="Offline cache synchronization status"
    )
    ip_address: Optional[str] = Field(
        default=None, max_length=45, description="Optional local IP for network diagnostic display"
    )


class KioskHeartbeatResponse(BaseModel):
    status: str = Field(default="ok", description="Acknowledgment status")
    kiosk_id: str = Field(..., description="Reporting kiosk ID")
    received_at: str = Field(..., description="ISO timestamp of heartbeat receipt")
    state: str = Field(..., description="Current operational state: online | maintenance")


class KioskResponse(BaseModel):
    id: str = Field(..., description="Unique kiosk identifier (e.g. KSK-001)")
    name: str = Field(..., description="Kiosk display name")
    location: str = Field(..., description="Physical deployment location")
    district: str = Field(..., description="Administrative district")
    state: str = Field(default="Maharashtra", description="State")
    pacs_name: str = Field(..., description="Host PACS society name")
    status: Literal["online", "offline", "maintenance"] = Field(
        ..., description="Operational status: online | offline | maintenance"
    )
    software_version: str = Field(default="v2.4.1", description="Software release version")
    ip_address: Optional[str] = Field(default=None, description="Reported network IP")
    installation_date: Optional[str] = Field(default=None, description="Deployment date")
    uptime_percent: Optional[float] = Field(default=None, description="Calculated availability percentage")
    health: KioskHealth = Field(default_factory=KioskHealth, description="Diagnostic subsystems")
    last_heartbeat: Optional[str] = Field(default=None, description="Last recorded heartbeat ISO timestamp")
    notes: Optional[str] = Field(default=None, description="Operational staff notes")
    created_at: str = Field(..., description="Creation ISO timestamp")
    updated_at: str = Field(..., description="Last update ISO timestamp")


class KioskListResponse(BaseModel):
    items: list[KioskResponse] = Field(..., description="List of monitored kiosks")
    total: int = Field(..., description="Total count matching filters")


class KioskUpdateRequest(BaseModel):
    """
    Controlled administrative update.
    Permits ONLY status and notes. All other fields are forbidden.
    """
    status: Optional[Literal["online", "offline", "maintenance"]] = Field(
        default=None,
        description="Operational status. Changing to 'maintenance' isolates the device.",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Operational field notes or reason for maintenance.",
    )

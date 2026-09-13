"""
Pydantic schemas for Phase 2C.1: Admin Analytics & Operational Insights.
All models represent strictly database-backed or derived analytics metrics.
"""
from __future__ import annotations

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class QueryTimelinePoint(BaseModel):
    date: str = Field(..., description="Date formatted as YYYY-MM-DD")
    queries: int = Field(..., description="Total user queries on this date")


class QuerySummaryMetrics(BaseModel):
    total: int = Field(..., description="Total lifetime user queries in database")
    today: int = Field(..., description="User queries submitted today (UTC)")
    this_week: int = Field(..., description="User queries submitted within the last 7 days")
    this_month: int = Field(..., description="User queries submitted within the last 30 days")
    timeline: List[QueryTimelinePoint] = Field(default_factory=list, description="Daily query volume for requested period")


class LanguageMetricItem(BaseModel):
    language: str = Field(..., description="Human-readable language name (e.g. Marathi, English, Hindi)")
    code: str = Field(..., description="ISO 639-1 language code (e.g. mr, en, hi)")
    count: int = Field(..., description="Number of user messages in this language")
    percentage: float = Field(..., description="Percentage of total user messages")
    color: str = Field(..., description="UI visual color representation")


class IntentMetricItem(BaseModel):
    intent: str = Field(..., description="Raw intent classification identifier")
    category: str = Field(..., description="Human-friendly domain category label")
    count: int = Field(..., description="Number of assistant turns generated for this intent")
    percentage: float = Field(..., description="Percentage of classified queries")
    color: str = Field(..., description="UI visual color representation")


class GrievanceAnalyticsSummary(BaseModel):
    total: int = Field(..., description="Total grievance records in Supabase grievances table")
    draft: int = Field(default=0, description="Grievances in draft status")
    submitted: int = Field(default=0, description="Grievances submitted by citizens")
    under_review: int = Field(default=0, description="Grievances actively under staff triage")
    resolved: int = Field(default=0, description="Grievances resolved")
    closed: int = Field(default=0, description="Grievances closed")
    priority: Optional[Dict[str, Any]] = Field(
        None,
        description="Priority breakdown or unavailable notice if not stored in core schema"
    )


class KnowledgeAnalyticsSummary(BaseModel):
    total: int = Field(..., description="Total official knowledge documents registered")
    draft: int = Field(default=0, description="Documents in draft status")
    under_review: int = Field(default=0, description="Documents under review")
    verified: int = Field(default=0, description="Documents verified by administrators")
    published: int = Field(default=0, description="Total published documents")
    published_current: int = Field(default=0, description="Current in-force published documents active in RAG")
    review_due: int = Field(default=0, description="Documents due for periodic review or expiring")
    superseded: int = Field(default=0, description="Older superseded versions excluded from current retrieval")


class KioskAnalyticsSummary(BaseModel):
    total: int = Field(..., description="Total deployed kiosks")
    online: int = Field(default=0, description="Kiosks with heartbeat in the last 15 minutes")
    offline: int = Field(default=0, description="Kiosks with stale or missing heartbeat")
    maintenance: int = Field(default=0, description="Kiosks in manual maintenance mode")


class UnavailableTelemetryMetrics(BaseModel):
    voice_vs_touch: Optional[float] = Field(None, description="Share of voice vs touch (not collected in telemetry)")
    kiosk_vs_web: Optional[float] = Field(None, description="Share of kiosk vs web (not collected in telemetry)")
    reason: str = Field(
        default="Client interaction channel (voice vs text and kiosk vs web) is not persisted in the message telemetry schema.",
        description="Reason why specific telemetry metrics are unavailable"
    )


class AdminAnalyticsOverviewResponse(BaseModel):
    status: str = Field(default="ok", description="Response status: ok | error")
    provenance: str = Field(default="REAL_DB", description="Data provenance: REAL_DB | REAL_API_DERIVED | EMPTY")
    period: str = Field(..., description="Requested reporting period (24h, 7d, 30d)")
    generated_at: str = Field(..., description="ISO 8601 UTC timestamp of metric calculation")
    queries: QuerySummaryMetrics = Field(..., description="User query volume and timeline")
    languages: List[LanguageMetricItem] = Field(default_factory=list, description="Multilingual adoption breakdown")
    intents: List[IntentMetricItem] = Field(default_factory=list, description="Top assistance categories and intents")
    grievances: GrievanceAnalyticsSummary = Field(..., description="Grievance redressal status distribution")
    knowledge: KnowledgeAnalyticsSummary = Field(..., description="Knowledge governance lifecycle metrics")
    kiosks: KioskAnalyticsSummary = Field(..., description="Hardware kiosk fleet status")
    channel_telemetry: UnavailableTelemetryMetrics = Field(
        default_factory=UnavailableTelemetryMetrics,
        description="Explaining metrics not captured in current telemetry"
    )


class KnowledgeGapItem(BaseModel):
    id: str = Field(..., description="Identifier for knowledge gap")
    topic: str = Field(..., description="Domain topic or query pattern with low coverage")
    frequency: int = Field(..., description="Observed query count or inquiry intensity")
    category: str = Field(..., description="Associated cooperative domain category")
    recommended_action: str = Field(..., description="Actionable recommendation for administrator")
    severity: str = Field(..., description="Severity level: high | medium | low")
    evidence: str = Field(..., description="Empirical evidence from database telemetry")


class AdminKnowledgeGapsResponse(BaseModel):
    status: str = Field(default="ok", description="Response status: ok | error")
    provenance: str = Field(default="REAL_API_DERIVED", description="Data provenance")
    total_gaps: int = Field(..., description="Total identified knowledge gap items")
    gaps: List[KnowledgeGapItem] = Field(default_factory=list, description="List of knowledge gap action items")
    generated_at: str = Field(..., description="ISO 8601 timestamp")

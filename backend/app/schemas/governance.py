from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

class DocumentType(str, Enum):
    ACT = "ACT"
    RULE = "RULE"
    BYLAW = "BYLAW"
    SCHEME = "SCHEME"
    GUIDELINE = "GUIDELINE"
    NOTIFICATION = "NOTIFICATION"
    MANUAL = "MANUAL"
    FAQ = "FAQ"
    UNKNOWN = "UNKNOWN"

class AuthorityLevel(str, Enum):
    CENTRAL_GOVERNMENT = "CENTRAL_GOVERNMENT"
    STATE_GOVERNMENT = "STATE_GOVERNMENT"
    NABARD = "NABARD"
    RBI = "RBI"
    NCDC = "NCDC"
    RCS = "RCS"
    DISTRICT_FEDERATION = "DISTRICT_FEDERATION"
    COOPERATIVE_SOCIETY = "COOPERATIVE_SOCIETY"
    UNKNOWN = "UNKNOWN"

class Jurisdiction(str, Enum):
    INDIA = "INDIA"
    MAHARASHTRA = "MAHARASHTRA"
    GUJARAT = "GUJARAT"
    KARNATAKA = "KARNATAKA"
    DELHI = "DELHI"
    UNKNOWN = "UNKNOWN"
    
class Applicability(str, Enum):
    ALL_COOPERATIVES = "ALL_COOPERATIVES"
    PACS = "PACS"
    HOUSING = "HOUSING"
    DAIRY = "DAIRY"
    FISHERY = "FISHERY"
    URBAN_BANK = "URBAN_BANK"
    RURAL_BANK = "RURAL_BANK"
    CREDIT = "CREDIT"
    UNKNOWN = "UNKNOWN"

class VerificationStatus(str, Enum):
    VERIFIED_OFFICIAL = "VERIFIED_OFFICIAL"
    OFFICIAL_NEEDS_VERIFICATION = "OFFICIAL_NEEDS_VERIFICATION"
    VERIFIED_EXPERT = "VERIFIED_EXPERT"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    NEEDS_VERIFICATION = "NEEDS_VERIFICATION"

class CurrentnessStatus(str, Enum):
    ACTIVE_IN_FORCE = "ACTIVE_IN_FORCE"
    AMENDED = "AMENDED"
    SUPERSEDED = "SUPERSEDED"
    DRAFT = "DRAFT"
    NEEDS_VERIFICATION = "NEEDS_VERIFICATION"
    UNKNOWN = "UNKNOWN"

class PrecedenceTier(int, Enum):
    TIER_1_STATUTORY_ACT = 100
    TIER_2_STATUTORY_RULE = 90
    TIER_3_APPLICABLE_BYLAW = 80
    TIER_4_SCHEME_GUIDELINE = 70
    TIER_5_MODEL_BYLAW_ADVISORY = 60
    TIER_6_EDUCATIONAL_FAQ = 50
    TIER_7_UNKNOWN = 10

class GovernanceMetadata(BaseModel):
    document_type: DocumentType = Field(default=DocumentType.UNKNOWN)
    authority_level: AuthorityLevel = Field(default=AuthorityLevel.UNKNOWN)
    jurisdiction: Jurisdiction = Field(default=Jurisdiction.UNKNOWN)
    applicability: List[Applicability] = Field(default_factory=lambda: [Applicability.UNKNOWN])
    year: Optional[int] = None
    verification_status: VerificationStatus = Field(default=VerificationStatus.NEEDS_VERIFICATION)
    currentness_status: CurrentnessStatus = Field(default=CurrentnessStatus.UNKNOWN)
    precedence_tier: PrecedenceTier = Field(default=PrecedenceTier.TIER_7_UNKNOWN)
    page_number: Optional[str] = None
    section_number: Optional[str] = None
    source_url: Optional[str] = None
    title: str = "Unknown Source"

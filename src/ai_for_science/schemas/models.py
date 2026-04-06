from enum import Enum

from pydantic import BaseModel


class Country(str, Enum):
    JAPAN = "japan"
    CHINA = "china"
    USA = "usa"
    EU = "eu"


class ComparisonDimension(str, Enum):
    STRATEGY_TYPE = "strategy_type"
    CORE_OBJECTIVE = "core_objective"
    INFRASTRUCTURE = "infrastructure"
    DATA_STRATEGY = "data_strategy"
    TALENT = "talent"
    INDUSTRY_LINKAGE = "industry_linkage"
    GOVERNANCE = "governance"
    INTERNATIONAL_COOPERATION = "international_cooperation"


class AgentType(str, Enum):
    ORCHESTRATOR = "orchestrator"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    INSIGHT = "insight"
    REFERENCE = "reference"


class UserQuery(BaseModel):
    question: str
    countries: list[Country] | None = None
    dimensions: list[ComparisonDimension] | None = None


class Reference(BaseModel):
    title: str
    source: str
    url: str
    country: Country | None = None
    description: str = ""


class ComparisonEntry(BaseModel):
    dimension: ComparisonDimension
    dimension_label: str
    country_data: dict[str, str]


class AgentMessage(BaseModel):
    sender: AgentType
    content: str
    references: list[Reference] = []
    comparisons: list[ComparisonEntry] = []
    metadata: dict = {}


class ServiceResponse(BaseModel):
    answer: str
    comparisons: list[ComparisonEntry] = []
    references: list[Reference] = []
    insights: list[str] = []

from __future__ import annotations

from pydantic import BaseModel, Field


class TeamMember(BaseModel):
    name: str = Field(
        description="Full name of the team or leadership member."
    )

    role: str = Field(
        description="Role or job title of the team member."
    )

    linkedin_url: str | None = Field(
        default=None,
        description="Public LinkedIn URL if discoverable."
    )


class CompanyIntelligence(BaseModel):
    company_name: str = Field(
        description="Official company name."
    )

    domain: str = Field(
        description="Company website domain."
    )

    company_overview: str = Field(
        description=(
            "A concise two-sentence overview of what the "
            "company does."
        )
    )

    target_audience: str = Field(
        description=(
            "Description of the company's target audience "
            "or ideal customer profile."
        )
    )

    public_contact_emails: list[str] = Field(
        default_factory=list,
        description=(
            "Generic or publicly available company contact "
            "email addresses discovered from public sources."
        )
    )

    leadership_team: list[TeamMember] = Field(
        default_factory=list,
        description=(
            "Leadership or relevant team members discovered "
            "from public company information."
        )
    )

    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Confidence in the extracted company intelligence, "
            "between 0.0 and 1.0."
        )
    )


class CompanyProcessingResult(BaseModel):
    """
    Represents the result of processing one company.

    A company can either have successful structured intelligence
    or a recorded error. This allows batch processing to continue
    when one website fails.
    """

    domain: str = Field(
        description="Company domain that was processed."
    )

    success: bool = Field(
        description="Whether processing completed successfully."
    )

    data: CompanyIntelligence | None = Field(
        default=None,
        description="Structured intelligence when successful."
    )

    error: str | None = Field(
        default=None,
        description="Error message when processing fails."
    )
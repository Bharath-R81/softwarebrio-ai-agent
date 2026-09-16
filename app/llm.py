from __future__ import annotations

import json
import os

from dotenv import load_dotenv
from groq import Groq

from app.models import CompanyIntelligence


load_dotenv()


class LLMEnricher:
    """
    Uses Groq to convert cleaned website information into
    structured company intelligence.
    """

    def __init__(
        self,
        model: str = "openai/gpt-oss-20b",
    ) -> None:
        self.api_key = os.getenv(
            "GROQ_API_KEY"
        )

        self.model = model

        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. "
                "Add it to your .env file."
            )

        self.client = Groq(
            api_key=self.api_key
        )

    def enrich(
        self,
        domain: str,
        website_text: str,
        public_emails: list[str],
        linkedin_urls: list[str],
    ) -> CompanyIntelligence:
        """
        Send cleaned website information to Groq and return
        validated structured company intelligence.
        """

        system_prompt = """
You are a company intelligence extraction agent.

Analyze the supplied public website information and return
ONLY valid JSON.

The JSON MUST contain exactly these top-level fields:

{
  "company_name": "string",
  "domain": "string",
  "company_overview": "string",
  "target_audience": "string",
  "public_contact_emails": [],
  "leadership_team": [],
  "confidence_score": 0.0
}

Rules:

1. Use only information supported by the supplied content.
2. Never invent company facts, people, roles, emails, or URLs.
3. company_name must contain the official company name when it
   is supported by the content.
4. domain must contain the supplied company domain.
5. company_overview must contain exactly two concise sentences.
6. target_audience must describe the company's target audience
   or ideal customer profile.
7. public_contact_emails must contain only valid public emails
   supplied in the input.
8. leadership_team must be a list of objects using exactly:
   {
     "name": "string",
     "role": "string",
     "linkedin_url": "string or null"
   }
9. Only include leadership/team members when their names and roles
   are supported by the supplied content.
10. Only use LinkedIn URLs supplied in the input.
11. confidence_score must be a number between 0.0 and 1.0.
12. If leadership information is unavailable, return [].
13. If a field cannot be determined, use an appropriate empty value.
14. Do not use alternative field names such as "confidence",
    "overview", "company", or "emails".
15. Do not include Markdown code fences.
16. Return JSON only.
"""

        user_prompt = f"""
Analyze this company.

DOMAIN:
{domain}

PUBLIC EMAILS DISCOVERED:
{json.dumps(public_emails)}

LINKEDIN URLS DISCOVERED:
{json.dumps(linkedin_urls)}

CLEANED WEBSITE CONTENT:
{website_text}
"""

        response = (
            self.client
            .chat
            .completions
            .create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                temperature=0,
                response_format={
                    "type": "json_object"
                },
            )
        )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        if not content:
            raise ValueError(
                "The LLM returned an empty response."
            )

        try:
            data = json.loads(
                content
            )

        except json.JSONDecodeError as exc:

            raise ValueError(
                "The LLM returned invalid JSON."
            ) from exc

        # ---------------------------------------------------------
        # Normalize common LLM field-name variations.
        # ---------------------------------------------------------

        if "company_name" not in data:

            data["company_name"] = data.get(
                "company",
                "",
            )

        if "company_overview" not in data:

            data["company_overview"] = data.get(
                "overview",
                "",
            )

        if "confidence_score" not in data:

            data["confidence_score"] = data.get(
                "confidence",
                0.0,
            )

        if "public_contact_emails" not in data:

            data["public_contact_emails"] = data.get(
                "emails",
                [],
            )

        if "leadership_team" not in data:

            data["leadership_team"] = data.get(
                "leadership",
                data.get(
                    "team",
                    [],
                ),
            )

        # Always trust the domain supplied by our scraper.
        data["domain"] = domain

        # ---------------------------------------------------------
        # Validate using Pydantic.
        # ---------------------------------------------------------

        try:

            return CompanyIntelligence.model_validate(
                data
            )

        except Exception as exc:

            raise ValueError(
                "The LLM response failed Pydantic validation."
            ) from exc
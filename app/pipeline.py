from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from app.llm import LLMEnricher
from app.models import CompanyProcessingResult
from app.scraper import WebsiteScraper


class CompanyIntelligencePipeline:
    """
    End-to-end company intelligence pipeline.

    Flow:
        Company domain
            ↓
        Playwright scraper
            ↓
        Clean website text
            ↓
        Relevant content selection
            ↓
        Groq LLM
            ↓
        Pydantic validation
            ↓
        Structured company intelligence
    """

    # Keep the LLM input small enough to avoid
    # Groq token-per-minute request limits.
    MAX_WEBSITE_CHARACTERS = 12_000

    def __init__(self) -> None:
        self.enricher = LLMEnricher()

    @classmethod
    def prepare_website_text(
        cls,
        scraped_data,
    ) -> str:
        """
        Prepare a compact representation of scraped
        website content.

        The homepage gets the highest priority because
        it normally contains the company's main description.

        Relevant subpages are then added within the
        character budget.
        """

        sections: list[str] = []

        remaining_characters = (
            cls.MAX_WEBSITE_CHARACTERS
        )

        # ---------------------------------------------------------
        # 1. Prioritize homepage content
        # ---------------------------------------------------------

        homepage_text = (
            scraped_data.homepage.text.strip()
        )

        if homepage_text:

            homepage_limit = min(
                len(homepage_text),
                5_000,
                remaining_characters,
            )

            sections.append(
                "=== HOMEPAGE ===\n"
                + homepage_text[:homepage_limit]
            )

            remaining_characters -= (
                homepage_limit
            )

        # ---------------------------------------------------------
        # 2. Add relevant subpage content
        # ---------------------------------------------------------

        for subpage in scraped_data.subpages:

            if remaining_characters <= 0:
                break

            subpage_text = (
                subpage.text.strip()
            )

            if not subpage_text:
                continue

            page_limit = min(
                len(subpage_text),
                2_000,
                remaining_characters,
            )

            sections.append(
                f"=== SUBPAGE: {subpage.url} ===\n"
                f"{subpage_text[:page_limit]}"
            )

            remaining_characters -= (
                page_limit
            )

        return "\n\n".join(
            sections
        )

    def process_company(
        self,
        domain: str,
    ) -> CompanyProcessingResult:
        """
        Process one company.

        Any error is captured and returned as a structured
        CompanyProcessingResult so that other companies
        can continue processing.
        """

        print("\n" + "=" * 70)
        print(
            f"PROCESSING COMPANY: {domain}"
        )
        print("=" * 70)

        try:

            with sync_playwright() as playwright:

                browser = (
                    playwright.chromium.launch(
                        headless=True
                    )
                )

                try:

                    # -------------------------------------------------
                    # Step 1: Scrape website
                    # -------------------------------------------------

                    scraper = WebsiteScraper(
                        browser
                    )

                    scraped_data = (
                        scraper.scrape(
                            domain
                        )
                    )

                    raw_text_length = (
                        len(
                            scraped_data
                            .homepage
                            .text
                        )
                        + sum(
                            len(page.text)
                            for page in (
                                scraped_data
                                .subpages
                            )
                        )
                    )

                    print(
                        f"\n[INFO] Raw cleaned website "
                        f"text: {raw_text_length} "
                        f"characters"
                    )

                    # -------------------------------------------------
                    # Step 2: Prepare compact LLM input
                    # -------------------------------------------------

                    website_text = (
                        self.prepare_website_text(
                            scraped_data
                        )
                    )

                    print(
                        f"[INFO] LLM website content: "
                        f"{len(website_text)} "
                        f"characters"
                    )

                    print(
                        f"[INFO] Public emails found: "
                        f"{len(scraped_data.emails)}"
                    )

                    print(
                        f"[INFO] LinkedIn URLs found: "
                        f"{len(scraped_data.linkedin_urls)}"
                    )

                    # -------------------------------------------------
                    # Step 3: Validate extracted content
                    # -------------------------------------------------

                    if not website_text.strip():

                        raise ValueError(
                            "No readable website content "
                            "was extracted."
                        )

                    # -------------------------------------------------
                    # Step 4: LLM enrichment
                    # -------------------------------------------------

                    print(
                        "\n[INFO] Sending website "
                        "content to Groq..."
                    )

                    intelligence = (
                        self.enricher.enrich(
                            domain=domain,
                            website_text=website_text,
                            public_emails=(
                                scraped_data.emails
                            ),
                            linkedin_urls=(
                                scraped_data.linkedin_urls
                            ),
                        )
                    )

                    print(
                        "[INFO] LLM enrichment "
                        "completed successfully."
                    )

                    return CompanyProcessingResult(
                        domain=domain,
                        success=True,
                        data=intelligence,
                        error=None,
                    )

                finally:

                    browser.close()

        except Exception as exc:

            print(
                f"\n[ERROR] Failed to process "
                f"{domain}: {exc}"
            )

            return CompanyProcessingResult(
                domain=domain,
                success=False,
                data=None,
                error=str(exc),
            )

    @staticmethod
    def save_results(
        results: list[
            CompanyProcessingResult
        ],
    ) -> Path:
        """
        Save all company processing results
        to output/results.json.
        """

        project_root = (
            Path(__file__)
            .resolve()
            .parent
            .parent
        )

        output_directory = (
            project_root / "output"
        )

        output_directory.mkdir(
            exist_ok=True
        )

        output_file = (
            output_directory
            / "results.json"
        )

        serialized_results = [
            result.model_dump()
            for result in results
        ]

        with output_file.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                serialized_results,
                file,
                indent=2,
                ensure_ascii=False,
            )

        return output_file


def main() -> None:
    """
    Process the three companies specified
    in the SoftwareBrio assignment.
    """

    target_domains = [
        "postman.com",
        "supabase.com",
        "vapi.ai",
    ]

    pipeline = (
        CompanyIntelligencePipeline()
    )

    results: list[
        CompanyProcessingResult
    ] = []

    # -------------------------------------------------------------
    # Process companies independently
    # -------------------------------------------------------------

    for domain in target_domains:

        result = (
            pipeline.process_company(
                domain
            )
        )

        results.append(
            result
        )

        if result.success:

            print(
                f"\n[SUCCESS] {domain} "
                "processed successfully."
            )

        else:

            print(
                f"\n[FAILED] {domain} "
                "was recorded as a failed result."
            )

    # -------------------------------------------------------------
    # Save results
    # -------------------------------------------------------------

    output_file = (
        pipeline.save_results(
            results
        )
    )

    successful_count = sum(
        1
        for result in results
        if result.success
    )

    failed_count = (
        len(results)
        - successful_count
    )

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)

    print(
        f"\nSuccessful companies: "
        f"{successful_count}"
    )

    print(
        f"Failed companies: "
        f"{failed_count}"
    )

    print(
        f"Total companies: "
        f"{len(results)}"
    )

    print(
        f"\nResults saved to: "
        f"{output_file}"
    )


if __name__ == "__main__":
    main()
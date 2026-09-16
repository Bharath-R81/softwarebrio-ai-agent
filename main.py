from __future__ import annotations

import sys

from app.pipeline import CompanyIntelligencePipeline


DEFAULT_TARGETS = [
    "postman.com",
    "supabase.com",
    "vapi.ai",
]


def main() -> None:
    """
    Command-line entry point for the SoftwareBrio
    company intelligence agent.

    Usage:

        python main.py

    Processes the three assignment targets.

        python main.py postman.com

    Processes one custom company domain.

        python main.py postman.com supabase.com

    Processes multiple custom company domains.
    """

    # ---------------------------------------------------------
    # Determine target domains
    # ---------------------------------------------------------

    if len(sys.argv) > 1:
        target_domains = sys.argv[1:]
    else:
        target_domains = DEFAULT_TARGETS

    print("=" * 70)
    print("SOFTWAREBRIO AUTONOMOUS COMPANY INTELLIGENCE AGENT")
    print("=" * 70)

    print("\nTarget companies:")

    for domain in target_domains:
        print(f"- {domain}")

    # ---------------------------------------------------------
    # Create pipeline
    # ---------------------------------------------------------

    pipeline = CompanyIntelligencePipeline()

    results = []

    # ---------------------------------------------------------
    # Process each company independently
    # ---------------------------------------------------------

    for domain in target_domains:

        result = pipeline.process_company(
            domain
        )

        results.append(
            result
        )

        if result.success:

            print(
                f"\n[SUCCESS] {domain} "
                "completed."
            )

        else:

            print(
                f"\n[FAILED] {domain} "
                "completed with an error."
            )

    # ---------------------------------------------------------
    # Save results
    # ---------------------------------------------------------

    output_file = (
        pipeline.save_results(
            results
        )
    )

    successful_count = sum(
        result.success
        for result in results
    )

    failed_count = (
        len(results)
        - successful_count
    )

    # ---------------------------------------------------------
    # Final summary
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("RUN SUMMARY")
    print("=" * 70)

    print(
        f"\nSuccessful: {successful_count}"
    )

    print(
        f"Failed: {failed_count}"
    )

    print(
        f"Total: {len(results)}"
    )

    print(
        f"\nOutput file:"
        f"\n{output_file}"
    )


if __name__ == "__main__":
    main()
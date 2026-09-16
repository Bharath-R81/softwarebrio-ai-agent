from playwright.sync_api import sync_playwright

from scraper import WebsiteScraper


def main() -> None:
    """
    Test scraper resilience against an HTTP 404 response.
    """

    test_url = (
        "https://postman.com/"
        "this-page-definitely-does-not-exist-123456789/"
    )

    print("=" * 70)
    print("HTTP ERROR HANDLING TEST")
    print("=" * 70)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True
        )

        try:
            scraper = WebsiteScraper(browser)

            result = scraper.scrape_page(
                test_url
            )

            print("\nRESULT")
            print("-" * 70)

            print(
                f"URL: {result.url}"
            )

            print(
                f"HTTP status: {result.status_code}"
            )

            print(
                f"Title: {result.title}"
            )

            print(
                f"Text length: {len(result.text)}"
            )

            print(
                f"Links found: {len(result.links)}"
            )

            print(
                f"Emails found: {len(result.emails)}"
            )

            print(
                f"LinkedIn URLs found: "
                f"{len(result.linkedin_urls)}"
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
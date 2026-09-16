from playwright.sync_api import sync_playwright

from scraper import WebsiteScraper


def main() -> None:
    target_domain = "postman.com"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        scraper = WebsiteScraper(browser)

        result = scraper.scrape(target_domain)

        print("\n" + "=" * 70)
        print("WEBSITE SCRAPING RESULT")
        print("=" * 70)

        print(f"\nDomain: {result.domain}")

        print("\nHOME PAGE")
        print("-" * 70)
        print(f"URL: {result.homepage.url}")
        print(f"Title: {result.homepage.title}")
        print(f"Text length: {len(result.homepage.text)} characters")

        print("\nSUBPAGES")
        print("-" * 70)
        print(f"Successfully scraped: {len(result.subpages)}")

        for index, subpage in enumerate(result.subpages, start=1):
            print(f"\n[{index}] {subpage.url}")
            print(f"Title: {subpage.title}")
            print(f"Text length: {len(subpage.text)} characters")

            if subpage.emails:
                print(f"Emails: {subpage.emails}")

            if subpage.linkedin_urls:
                print(
                    f"LinkedIn URLs: {subpage.linkedin_urls}"
                )

        print("\n" + "=" * 70)
        print("EXTRACTED CONTACT INFORMATION")
        print("=" * 70)

        print("\nPublic emails:")
        if result.emails:
            for email in result.emails:
                print(f"- {email}")
        else:
            print("- None found")

        print("\nLinkedIn URLs:")
        if result.linkedin_urls:
            for url in result.linkedin_urls:
                print(f"- {url}")
        else:
            print("- None found")

        browser.close()


if __name__ == "__main__":
    main()
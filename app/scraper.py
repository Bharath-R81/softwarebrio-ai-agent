from __future__ import annotations

import html
import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import Browser, Page


@dataclass
class ScrapedPage:
    url: str
    title: str
    text: str
    links: list[str]
    emails: list[str]
    linkedin_urls: list[str]
    status_code: int | None = None


@dataclass
class ScrapedWebsite:
    domain: str
    homepage: ScrapedPage
    subpages: list[ScrapedPage]
    emails: list[str]
    linkedin_urls: list[str]


class WebsiteScraper:
    def __init__(self, browser: Browser) -> None:
        self.browser = browser

    @staticmethod
    def normalize_url(domain: str) -> str:
        """
        Convert a domain or URL into a normalized homepage URL.
        """

        domain = domain.strip()

        if not domain.startswith(
            ("http://", "https://")
        ):
            domain = f"https://{domain}"

        parsed = urlparse(domain)

        if not parsed.netloc:
            raise ValueError(
                f"Invalid domain: {domain}"
            )

        return (
            f"{parsed.scheme}://"
            f"{parsed.netloc}/"
        )

    def fetch_page(
        self,
        url: str,
    ) -> tuple[Page, int | None]:
        """
        Open a URL using Playwright and return the page
        together with its HTTP status code.
        """

        page = self.browser.new_page()

        try:
            response = page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30_000,
            )

            status_code = (
                response.status
                if response is not None
                else None
            )

            return page, status_code

        except Exception:
            page.close()
            raise

    @staticmethod
    def extract_clean_text(
        page: Page,
    ) -> str:
        """
        Extract readable text from a webpage while removing
        scripts, styles, SVGs, navigation and footer boilerplate.
        """

        html_content = page.content()

        soup = BeautifulSoup(
            html_content,
            "html.parser",
        )

        for element in soup(
            [
                "script",
                "style",
                "noscript",
                "svg",
                "nav",
                "footer",
            ]
        ):
            element.decompose()

        text = soup.get_text(
            separator=" ",
            strip=True,
        )

        return " ".join(
            text.split()
        )

    @staticmethod
    def extract_emails(
        page: Page,
    ) -> list[str]:
        """
        Extract valid public email addresses from:
        - webpage HTML
        - mailto links
        """

        html_content = page.content()

        decoded_html = html.unescape(
            html_content
        )

        decoded_html = re.sub(
            r"(?:\\u003e|u003e)+",
            "",
            decoded_html,
            flags=re.IGNORECASE,
        )

        email_pattern = re.compile(
            r"\b"
            r"[A-Za-z0-9._%+-]+"
            r"@"
            r"[A-Za-z0-9.-]+"
            r"\."
            r"[A-Za-z]{2,}"
            r"\b"
        )

        emails: set[str] = set()

        # Extract from page source.
        for match in email_pattern.findall(
            decoded_html
        ):
            email = match.strip().lower()

            if email_pattern.fullmatch(email):
                emails.add(email)

        # Extract mailto links.
        for anchor in page.locator(
            "a[href^='mailto:']"
        ).all():

            href = anchor.get_attribute(
                "href"
            )

            if not href:
                continue

            email = html.unescape(
                href
            )

            email = re.sub(
                r"(?:\\u003e|u003e)+",
                "",
                email,
                flags=re.IGNORECASE,
            )

            email = email.replace(
                "mailto:",
                "",
            )

            email = email.split(
                "?"
            )[0]

            email = email.strip().lower()

            if email_pattern.fullmatch(
                email
            ):
                emails.add(email)

        return sorted(emails)

    @staticmethod
    def extract_linkedin_urls(
        page: Page,
    ) -> list[str]:
        """
        Extract LinkedIn profile or company URLs
        from webpage links.
        """

        linkedin_urls: set[str] = set()

        for anchor in page.locator(
            "a[href]"
        ).all():

            href = anchor.get_attribute(
                "href"
            )

            if not href:
                continue

            absolute_url = urljoin(
                page.url,
                href,
            )

            parsed_url = urlparse(
                absolute_url
            )

            if "linkedin.com" in (
                parsed_url.netloc.lower()
            ):
                clean_url = (
                    parsed_url
                    ._replace(
                        query="",
                        fragment="",
                    )
                    .geturl()
                )

                linkedin_urls.add(
                    clean_url
                )

        return sorted(
            linkedin_urls
        )

    @staticmethod
    def discover_relevant_links(
        page: Page,
        base_url: str,
    ) -> list[str]:
        """
        Discover relevant internal pages such as:
        about, team, company, contact, pricing and leadership.
        """

        html_content = page.content()

        soup = BeautifulSoup(
            html_content,
            "html.parser",
        )

        base_domain = (
            urlparse(
                base_url
            )
            .netloc
            .lower()
        )

        keywords = (
            "about",
            "team",
            "company",
            "contact",
            "pricing",
            "leadership",
            "people",
        )

        relevant_links: list[str] = []

        for anchor in soup.find_all(
            "a",
            href=True,
        ):

            href = anchor.get(
                "href"
            )

            if not isinstance(
                href,
                str,
            ):
                continue

            absolute_url = urljoin(
                base_url,
                href,
            )

            parsed_url = urlparse(
                absolute_url
            )

            if (
                parsed_url.netloc.lower()
                != base_domain
            ):
                continue

            clean_url = (
                parsed_url
                ._replace(
                    fragment=""
                )
                .geturl()
            )

            path_and_text = (
                f"{parsed_url.path} "
                f"{anchor.get_text(' ', strip=True)}"
            ).lower()

            if any(
                keyword in path_and_text
                for keyword in keywords
            ):

                if clean_url not in relevant_links:
                    relevant_links.append(
                        clean_url
                    )

        return relevant_links[:10]

    def scrape_page(
        self,
        url: str,
    ) -> ScrapedPage:
        """
        Scrape one webpage and extract:
        - HTTP status
        - title
        - clean text
        - relevant links
        - public emails
        - LinkedIn URLs

        Any failure is handled gracefully.
        """

        page: Page | None = None

        try:
            page, status_code = (
                self.fetch_page(url)
            )

            # Explicitly report HTTP errors.
            if (
                status_code is not None
                and status_code >= 400
            ):
                print(
                    f"[WARNING] HTTP {status_code}: "
                    f"{url}"
                )

            title = page.title()

            text = (
                self.extract_clean_text(
                    page
                )
            )

            links = (
                self.discover_relevant_links(
                    page,
                    url,
                )
            )

            emails = (
                self.extract_emails(
                    page
                )
            )

            linkedin_urls = (
                self.extract_linkedin_urls(
                    page
                )
            )

            return ScrapedPage(
                url=url,
                title=title,
                text=text,
                links=links,
                emails=emails,
                linkedin_urls=linkedin_urls,
                status_code=status_code,
            )

        except Exception as exc:

            print(
                f"[WARNING] Failed to scrape "
                f"{url}: {exc}"
            )

            return ScrapedPage(
                url=url,
                title="",
                text="",
                links=[],
                emails=[],
                linkedin_urls=[],
                status_code=None,
            )

        finally:

            if page is not None:
                page.close()

    def scrape(
        self,
        domain: str,
    ) -> ScrapedWebsite:
        """
        Crawl a company's homepage and relevant internal
        subpages.
        """

        homepage_url = (
            self.normalize_url(
                domain
            )
        )

        print(
            f"[INFO] Scraping homepage: "
            f"{homepage_url}"
        )

        homepage = (
            self.scrape_page(
                homepage_url
            )
        )

        relevant_links = (
            homepage.links
        )

        print(
            f"[INFO] Discovered "
            f"{len(relevant_links)} "
            f"relevant internal links."
        )

        subpages: list[
            ScrapedPage
        ] = []

        for index, link in enumerate(
            relevant_links,
            start=1,
        ):

            print(
                f"[INFO] Scraping subpage "
                f"{index}/"
                f"{len(relevant_links)}: "
                f"{link}"
            )

            subpage = (
                self.scrape_page(
                    link
                )
            )

            if subpage.text:
                subpages.append(
                    subpage
                )

        # Combine emails.
        all_emails: set[str] = set(
            homepage.emails
        )

        for subpage in subpages:
            all_emails.update(
                subpage.emails
            )

        # Combine LinkedIn URLs.
        all_linkedin_urls: set[str] = set(
            homepage.linkedin_urls
        )

        for subpage in subpages:
            all_linkedin_urls.update(
                subpage.linkedin_urls
            )

        return ScrapedWebsite(
            domain=domain,
            homepage=homepage,
            subpages=subpages,
            emails=sorted(
                all_emails
            ),
            linkedin_urls=sorted(
                all_linkedin_urls
            ),
        )
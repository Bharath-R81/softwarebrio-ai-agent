# SoftwareBrio Autonomous Company Intelligence Agent

A Python-based autonomous web intelligence pipeline that crawls public company websites, extracts clean website content, discovers public contact information and LinkedIn URLs, and uses an LLM to generate structured company intelligence.

## Overview

The agent accepts company domains and performs this workflow:

Company Domain
→ Playwright Browser
→ Homepage and Relevant Subpages
→ Clean Text Extraction
→ Public Email and LinkedIn Extraction
→ LLM Enrichment
→ Pydantic Validation
→ Structured JSON Output

The pipeline processes each company independently so that a failure on one website does not stop the remaining companies.

## Assignment Targets

The implementation supports:

- `postman.com`
- `supabase.com`
- `vapi.ai`

## Features

- Autonomous website crawling with Playwright
- JavaScript-capable browser rendering
- Relevant internal page discovery
- Clean text extraction using BeautifulSoup
- Public email extraction
- Public LinkedIn URL extraction
- LLM-based company intelligence extraction
- Structured output validation with Pydantic
- Confidence scoring
- Per-company error handling
- JSON result generation
- Command-line support for custom domains

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core implementation |
| Playwright | Browser automation and web crawling |
| BeautifulSoup | HTML parsing and text extraction |
| Groq | LLM inference |
| GPT-OSS-20B | Company intelligence extraction |
| Pydantic | Structured data validation |
| python-dotenv | Environment variable management |
| JSON | Result storage |

## Project Structure

```text
softwarebrio-ai-agent/
│
├── app/
│   ├── __init__.py
│   ├── llm.py
│   ├── models.py
│   ├── pipeline.py
│   ├── scraper.py
│   ├── test_scraper.py
│   └── test_error_handling.py
│
├── output/
│   └── results.json
│
├── .env
├── .env.example
├── .gitignore
├── main.py
├── README.md
└── requirements.txt
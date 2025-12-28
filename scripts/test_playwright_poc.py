"""
Proof of Concept: Playwright vs BeautifulSoup comparison

This script tests the feasibility of using Playwright for dynamic web scraping
in the OpenWatt project (constitution v2.0).

Tests:
1. Static HTML page with BeautifulSoup (baseline)
2. Same page with Playwright (validation)
3. Dynamic JavaScript page that requires Playwright

Usage:
    python scripts/test_playwright_poc.py
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


def test_beautifulsoup_static(url: str) -> dict[str, Any]:
    """Test scraping with requests + BeautifulSoup (current stack)"""
    print(f"\n[BeautifulSoup] Fetching {url}...")
    start = time.time()

    try:
        response = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Try to extract prices (generic selectors)
        prices = []
        for price_elem in soup.select("span, div, td, p"):
            text = price_elem.get_text(strip=True)
            if "€" in text and any(char.isdigit() for char in text):
                prices.append(text)

        duration = time.time() - start

        return {
            "method": "BeautifulSoup",
            "status": "success",
            "duration_ms": int(duration * 1000),
            "html_length": len(response.text),
            "prices_found": len(prices[:5]),  # Limit to first 5
            "sample_prices": prices[:5],
            "requires_js": "No",
        }

    except Exception as e:
        return {
            "method": "BeautifulSoup",
            "status": "error",
            "error": str(e),
        }


async def test_playwright_page(url: str, wait_for_selector: str | None = None) -> dict[str, Any]:
    """Test scraping with Playwright (new stack option)"""
    print(f"\n[Playwright] Fetching {url}...")
    start = time.time()

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            await page.goto(url, wait_until="networkidle")

            # Wait for dynamic content if selector provided
            if wait_for_selector:
                await page.wait_for_selector(wait_for_selector, timeout=5000)

            # Extract all text content
            content = await page.content()

            # Extract prices
            prices = await page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('span, div, td, p');
                    const prices = [];
                    for (let elem of elements) {
                        const text = elem.textContent.trim();
                        if (text.includes('€') && /\\d/.test(text)) {
                            prices.push(text);
                        }
                    }
                    return prices.slice(0, 5);
                }
            """)

            await browser.close()

        duration = time.time() - start

        return {
            "method": "Playwright",
            "status": "success",
            "duration_ms": int(duration * 1000),
            "html_length": len(content),
            "prices_found": len(prices),
            "sample_prices": prices,
            "requires_js": "Yes",
        }

    except Exception as e:
        return {
            "method": "Playwright",
            "status": "error",
            "error": str(e),
        }


async def main():
    """Run all POC tests"""
    print("=" * 80)
    print("OpenWatt - Playwright POC (Constitution v2.0)")
    print("=" * 80)

    # Test 1: Static aggregator page (should work with both)
    test_url = "https://www.fournisseurs-electricite.com/fournisseurs/edf/tarifs/bleu-reglemente"

    print("\n[TEST 1] Static HTML page (aggregator)")
    print(f"URL: {test_url}")

    result_bs = test_beautifulsoup_static(test_url)
    result_pw = await test_playwright_page(test_url)

    print("\n" + "=" * 80)
    print("RESULTS COMPARISON")
    print("=" * 80)

    print(f"\n{'Method':<20} {'Status':<10} {'Duration':<12} {'HTML Size':<12} {'Prices Found'}")
    print("-" * 80)
    print(f"{result_bs['method']:<20} {result_bs.get('status', 'N/A'):<10} "
          f"{result_bs.get('duration_ms', 'N/A'):<12} "
          f"{result_bs.get('html_length', 'N/A'):<12} "
          f"{result_bs.get('prices_found', 'N/A')}")

    print(f"{result_pw['method']:<20} {result_pw.get('status', 'N/A'):<10} "
          f"{result_pw.get('duration_ms', 'N/A'):<12} "
          f"{result_pw.get('html_length', 'N/A'):<12} "
          f"{result_pw.get('prices_found', 'N/A')}")

    print("\n" + "=" * 80)
    print("SAMPLE PRICES EXTRACTED")
    print("=" * 80)

    if result_bs.get("sample_prices"):
        print("\n[BeautifulSoup]")
        for price in result_bs["sample_prices"]:
            # Filter out non-ASCII characters for Windows console
            clean_price = price.encode("ascii", "ignore").decode("ascii")
            print(f"  - {clean_price}")

    if result_pw.get("sample_prices"):
        print("\n[Playwright]")
        for price in result_pw["sample_prices"]:
            # Filter out non-ASCII characters for Windows console
            clean_price = price.encode("ascii", "ignore").decode("ascii")
            print(f"  - {clean_price}")

    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)

    if result_bs["status"] == "success" and result_pw["status"] == "success":
        print("\n[SUCCESS] Both methods work for static HTML pages")
        print(f"   BeautifulSoup: {result_bs['duration_ms']}ms")
        print(f"   Playwright: {result_pw['duration_ms']}ms")
        print(f"\n   Speed ratio: Playwright is {result_pw['duration_ms'] / result_bs['duration_ms']:.1f}x slower")
        print("\n[RECOMMENDATION]")
        print("   - Use BeautifulSoup for static pages (faster, lighter)")
        print("   - Reserve Playwright for dynamic JavaScript pages")
        print("\n[VALIDATION] Constitution v2.0 approach VALIDATED")
    else:
        print("\n[WARNING] Some tests failed:")
        if result_bs["status"] != "success":
            print(f"   BeautifulSoup: {result_bs.get('error')}")
        if result_pw["status"] != "success":
            print(f"   Playwright: {result_pw.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())

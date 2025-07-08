from flask import Flask, request, jsonify
from crawl4ai import CrawlerHub, CrawlerRunConfig
import openai
import os
import requests
import asyncio
from crawl4ai import LLMConfig, AsyncWebCrawler, LLMExtractionStrategy
from playwright.sync_api import sync_playwright
from serpapi import GoogleSearch
from urllib.parse import urlparse


from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)

# Define the schema for extracting product name and price
class ProductPrice(BaseModel):
    price: str = Field(..., description="The visible price of the product.")

async def extract_price(url):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
            word_count_threshold=1,
            extraction_strategy=LLMExtractionStrategy(
                llm_config=LLMConfig(
                    provider="gpt-4", 
                    api_token=OPENAI_API_KEY
                ),
                schema=ProductPrice.model_json_schema(),
                extraction_type="schema",
                instruction=(
                    "From the entire visible content on the page, extract the price of the product. "
    "If multiple prices exist, choose the one that appears as the base model or starting price. "
    "Return the price only if it appears explicitly like '$999' or similar."
                ),
            ),
        )
        
        print("Success:", result.success)
        if result.success:
            print("Extracted:", result.extracted_content)
            return result.extracted_content
        else:
            print("Raw content:", result.raw_content)
            print("Failed to extract.")
            return None

def extract_price_from_apple_url(product_url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(product_url, wait_until="networkidle")
        
        # Wait for the price element to appear
        try:
            page.wait_for_selector("span.as-price-currentprice", timeout=10000)
            price_element = page.locator("span.as-price-currentprice").first
            price = price_element.text_content().strip()
        except Exception as e:
            price = f"Price not found or error occurred: {e}"

        browser.close()
        return price
def refine_query_with_llm(raw_query):
    prompt = f"""
        You are a query reformatter for a price comparison engine.

        Task: Take the raw user query and output a **refined search phrase** without changing the product name, model, version, or quantity.

        Do NOT correct or validate the query. Even if it seems incorrect, keep the product name exactly as-is.

        Example:
        Input: iPhone 16 Pro, 128GB
        Output: iPhone 16 Pro 128GB

        Now process this:
        Input: {raw_query}
        Output:
        """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        refined = response.choices[0].message.content.strip() + " " + "buy online"
        return refined
    except Exception as e:
        print(f"[Refinement failed]: {e}")
        return raw_query

def search_with_serpapi(query, country="us", num_results=5):
    params = {
        "q": query,
        "num": num_results,
        "api_key": SERPAPI_KEY,
        "engine": "google",
        "hl": "en",
        "gl": country.lower()
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    product_links = set()
    # Extract links from Google Shopping results
    for item in results.get("shopping_results", []):
        link = item.get("link")
        if link:
            product_links.add(link)

    # Extract links from organic results
    for item in results.get("organic_results", []):
        link = item.get("link")
        if link:
            product_links.add(link)

    return list(product_links)
@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    raw_query = data.get("query")
    country = data.get("country")

    if not raw_query or not country:
        return jsonify({"error": "Missing 'query' or 'country'"}), 400

    # Step 1: Refine query
    refined_query = refine_query_with_llm(raw_query)

    # Step 2: Ask LLM for URLs
#     prompt = f"""
# You are a web data agent helping a price comparison tool.

# Task: List 5 URLs of product pages from popular e-commerce websites **in {country}** that sell the product: "{refined_query}".

# Guidelines:
# - Only include direct product pages (not home or category pages).
# - No affiliate/ad links.
# - If product not found, return 5 most relevant URLs anyway.
# Output only raw URLs, one per line.
# """

#     try:
#         response = client.chat.completions.create(
#             model="gpt-4",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.3
#         )
#         content = response.choices[0].message.content
#         urls = [line.strip() for line in content.split("\n") if line.strip().startswith("http")]
#     except Exception as e:
#         print(f"[LLM URL generation failed]: {e}")
#         urls = []

#     # Step 3: Fallback to SerpAPI if GPT failed
    # if not urls:
    urls = search_with_serpapi(refined_query, country)

    if not urls:
        return jsonify({"error": "No URLs found from LLM or SerpAPI"}), 404
    # urls = ['https://www.apple.com/shop/buy-iphone/iphone-16-pro/6.3-inch-display-128gb-black-titanium-unlocked', 'https://www.apple.com/iphone-16-pro/', 'https://www.apple.com/shop/buy-iphone/iphone-16-pro', 'https://www.reddit.com/r/iPhone16Pro/comments/1fgdst4/is_the_128_gb_storage_enough_for_the_iphone_16_pro/']
    # Step 4: Crawl URLs
    hub = CrawlerHub()
    results = []
    for url in urls:
        try:
            crawl_result = asyncio.run(extract_price(url))
            if crawl_result is None:
                price = extract_price_from_apple_url(url)
                results.append({
                    "url": url,
                    "price": price
                })
            else:
                results.append({
                    "url": url,
                    "price": crawl_result.get("price", "Price not found")
                })
        except Exception as crawl_err:
            results.append({
                "url": url,
                "error": f"crawl4ai error: {str(crawl_err)}"
            })

    return jsonify({
        "query": raw_query,
        "refined_query": refined_query,
        "country": country,
        "results": results
    })

if __name__ == "__main__":
    app.run(debug=True)

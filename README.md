# 🛍️ Price Comparator

A Python-based tool to compare product prices across multiple online retailers using web scraping and APIs. Easily find the best deal on a product from major e-commerce platforms.

---

## 🚀 Features

- 🔍 **Product Search** via SERP API  
- 🌐 **Web Scraping** with Playwright for accurate price extraction  
- 🤖 **Structured Extraction** using LLMs (via crawl4ai)  
- 🛒 **Product Link Collection** from multiple sources  
- ✅ Compares prices across different retailers  
- 📦 Output as structured JSON  

---

## 🧰 Technologies Used

- `Playwright` — Headless browser automation  
- `crawl4ai` — LLM-based content extraction  
- `SERP API` — Google search results via API  
- `Pydantic` — Schema-based data models  
- `Asyncio` — Concurrency for fast crawling  

---

## 📦 Installation

```bash
git clone https://github.com/yourusername/price-comparator.git
cd price-comparator
make install
make run
curl -X POST http://127.0.0.1:5000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "iPhone 16 Pro, 128GB", "country": "US"}'


```
Response

curl -X POST http://127.0.0.1:5000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "iPhone 16 Pro, 128GB", "country": "US"}'

{
  "country": "US",
  "query": "iPhone 16 Pro, 128GB",
  "refined_query": "iPhone 16 Pro 128GB buy online",
  "results": [
    {
      "price": "$999.00",
      "url": "https://www.apple.com/shop/buy-iphone/iphone-16-pro/6.3-inch-display-128gb-black-titanium-unlocked"
    },
    {
      "error": "crawl4ai error: Page.goto: Timeout 30000ms exceeded.\nCall log:\n  - navigating to \"https://www.amazon.com/Apple-iPhone-Version-128GB-Titanium/dp/B0DHJG6JPH\", waiting until \"networkidle\"\n",
      "url": "https://www.amazon.com/Apple-iPhone-Version-128GB-Titanium/dp/B0DHJG6JPH"
    },
    {
      "price": "Price not found or error occurred: Page.wait_for_selector: Timeout 10000ms exceeded.\nCall log:\n  - waiting for locator(\"span.as-price-currentprice\") to be visible\n",
      "url": "https://www.apple.com/shop/buy-iphone/iphone-16-pro"
    }
  ]
}

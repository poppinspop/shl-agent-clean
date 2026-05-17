import requests
from bs4 import BeautifulSoup
import json
import time

BASE_URL = "https://www.shl.com/solutions/products/product-catalog/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def get_catalog_page():
    response = requests.get(BASE_URL, headers=HEADERS)
    response.raise_for_status()
    return response.text


def extract_test_links(html):
    soup = BeautifulSoup(html, "lxml")
    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]

        # ONLY actual assessment pages
        if "/products/product-catalog/view/" in href:
            full_url = href if href.startswith("http") else f"https://www.shl.com{href}"
            links.add(full_url)

    return list(links)


def scrape_test_page(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        title_tag = soup.find("h1")
        title = title_tag.text.strip() if title_tag else "Unknown"

        container = soup.find("div", attrs={"data-course-id": True})

        if not container:
            print(f"No structured container found for {url}")
            return None

        fields = {}

        rows = container.find_all(
            "div", class_="product-catalogue-training-calendar__row"
        )

        for row in rows:
            heading = row.find("h4")
            paragraph = row.find("p")

            if heading and paragraph:
                key = heading.text.strip().lower().replace(" ", "_")
                value = paragraph.text.strip()

                fields[key] = value

        # test type extraction
        test_type_span = container.find("span", class_="product-catalogue__key")

        test_type = test_type_span.text.strip() if test_type_span else None

        return {
            "name": title,
            "url": url,
            "description": fields.get("description"),
            "job_levels": fields.get("job_levels"),
            "languages": fields.get("languages"),
            "assessment_length": fields.get("assessment_length"),
            "test_type": test_type,
        }

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


def main():
    all_links = set()

    offsets = range(0, 400, 12)

    for offset in offsets:
        url = f"https://www.shl.com/solutions/products/product-catalog/?start={offset}&type=1"

        print(f"Scraping catalog page: {url}")

        try:
            response = requests.get(url, headers=HEADERS, timeout=15)

            if response.status_code == 502:
                print(f"No more valid pages at offset {offset}. Stopping scrape.")
                break

            response.raise_for_status()

        except Exception as e:
            print(f"Error at offset {offset}: {e}")
            break

        links = extract_test_links(response.text)

        if not links:
            print("No more links found. Stopping.")
            break

        all_links.update(links)
        print(f"Total links so far: {len(all_links)}")

        time.sleep(2)

    print(f"\nFinal total assessment links: {len(all_links)}")

    results = []

    for i, link in enumerate(all_links):
        print(f"[{i+1}/{len(all_links)}] Scraping {link}")

        data = scrape_test_page(link)

        if data:
            results.append(data)

        time.sleep(1)

    with open("catalog.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Saved {len(results)} assessments")


if __name__ == "__main__":
    main()

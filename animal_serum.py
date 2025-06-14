import os
import re
import csv
import requests
from bs4 import BeautifulSoup

# Configuration
BASE_URL = "https://www.equitech-bio.com"
CATEGORY = "animal-serum"  # Change category here
SAVE_DIR = CATEGORY
CSV_FILE = f"{CATEGORY}_images.csv"
os.makedirs(SAVE_DIR, exist_ok=True)

def slugify(text):
    text = text.strip().lower()
    text = re.sub(r'\s+', '_', text)
    text = re.sub(r'[^\w\-_.]', '', text)
    return text[:100]

def download_image(img_url, alt_text, counter):
    try:
        response = requests.get(img_url, timeout=10)
        response.raise_for_status()
        ext = os.path.splitext(img_url)[1].split("?")[0] or ".jpg"
        slug = slugify(alt_text) if alt_text else f"image_{counter}"
        filename = f"{counter:03d}_{slug}{ext}"
        path = os.path.join(SAVE_DIR, filename)
        with open(path, "wb") as f:
            f.write(response.content)
        print(f"✔️ Saved: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Failed to download {img_url}: {e}")
        return None

def get_hd_image_from_product_page(product_url):
    try:
        res = requests.get(product_url, timeout=10)
        if res.status_code != 200:
            print(f"❌ Failed to access {product_url}")
            return None, None
        soup = BeautifulSoup(res.content, "html.parser")

        a_tag = soup.select_one("div.woocommerce-product-gallery__image a")
        img_url = a_tag.get("href") if a_tag else None

        alt_tag = soup.select_one("h1.product_title.entry-title")
        alt_text = alt_tag.text.strip() if alt_tag else "product"

        return img_url, alt_text
    except Exception as e:
        print(f"❌ Error scraping {product_url}: {e}")
        return None, None

def scrape_category_pages():
    counter = 1
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Image URL', 'Saved Image Name']  # Only these two
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for page_num in range(1, 20):
            url = f"{BASE_URL}/product-category/{CATEGORY}/"
            if page_num > 1:
                url += f"/page/{page_num}/"
            print(f"\n🔍 Scraping: {url}")
            res = requests.get(url)
            if res.status_code != 200:
                print(f"🛑 Page {page_num} not found. Stopping.")
                break

            soup = BeautifulSoup(res.content, "html.parser")
            product_links = soup.select("li.product a[href]")
            product_urls = {a['href'] for a in product_links if '/product/' in a['href']}
            if not product_urls:
                print("🛑 No product links found, stopping.")
                break

            for product_url in product_urls:
                print(f"➡️  Visiting: {product_url}")
                img_url, alt_text = get_hd_image_from_product_page(product_url)
                if img_url:
                    saved_filename = download_image(img_url, alt_text, counter)
                    if saved_filename:
                        writer.writerow({
                            'Image URL': img_url,
                            'Saved Image Name': saved_filename
                        })
                        counter += 1

if __name__ == "__main__":
    scrape_category_pages()

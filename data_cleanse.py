import json
import re
from datetime import datetime

RAW_FILE_PATH = "small-amazon-meta.txt"
OUTPUT_FILE_PATH = "amazon_cleaned.jsonl"

RE_CATEGORY = re.compile(r"\|?([^|\[]+)\[(\d+)\]")


def parse_category_path(cat_line: str) -> list[dict]:
    """Extract category name and ID pairs from pipe-delimited hierarchy."""
    categories = []
    matches = RE_CATEGORY.findall(cat_line)
    for cat_name, cat_id in matches:
        categories.append({"id": int(cat_id), "name": cat_name.strip()})
    return categories


def parse_amazon_meta(file_path: str):
    """Generator streaming parsed, cleaned, and reduced Amazon product records."""
    current_item = None
    collecting_categories = False
    collecting_reviews = False

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line_str = line.strip()

            if not line_str or line_str.startswith("#") or line_str.startswith("Total"):
                continue

            # New product boundary
            if line_str.startswith("Id:"):
                if current_item:
                    # Data Reduction: omit discontinued items
                    if not current_item.get("discontinued", False):
                        yield current_item
                item_id = int(line_str.split(":", 1)[1].strip())
                current_item = {
                    "id": item_id,
                    "asin": None,
                    "title": None,
                    "group": None,
                    "salesrank": None,
                    "similar_count": 0,
                    "similar_asins": [],
                    "categories": [],
                    "reviews_summary": {},
                    "reviews": [],
                    "discontinued": False,
                }
                collecting_categories = False
                collecting_reviews = False
                continue

            if current_item is None:
                continue

            if line_str.startswith("ASIN:"):
                current_item["asin"] = line_str.split(":", 1)[1].strip()
                continue

            if "discontinued product" in line_str:
                current_item["discontinued"] = True
                continue

            if line_str.startswith("title:"):
                current_item["title"] = line_str.split("title:", 1)[1].strip()
                continue

            if line_str.startswith("group:"):
                current_item["group"] = line_str.split("group:", 1)[1].strip()
                continue

            if line_str.startswith("salesrank:"):
                current_item["salesrank"] = int(
                    line_str.split("salesrank:", 1)[1].strip()
                )
                continue

            if line_str.startswith("similar:"):
                tokens = line_str.split()
                # tokens[0] is 'similar:', tokens[1] is the count
                current_item["similar_count"] = int(tokens[1])
                current_item["similar_asins"] = tokens[2:]
                continue

            if line_str.startswith("categories:"):
                collecting_categories = True
                collecting_reviews = False
                continue

            if line_str.startswith("reviews:"):
                collecting_categories = False
                collecting_reviews = True
                # Format: reviews: total: 2  downloaded: 2  avg rating: 5
                parts = re.findall(
                    r"total:\s*(\d+)\s+downloaded:\s*(\d+)\s+avg rating:\s*([\d\.]+)",
                    line_str,
                )
                if parts:
                    total, downloaded, avg_r = parts[0]
                    current_item["reviews_summary"] = {
                        "total": int(total),
                        "downloaded": int(downloaded),
                        "avg_rating": float(avg_r),
                    }
                continue

            # Process category lines
            if collecting_categories and line_str.startswith("|"):
                current_item["categories"].append(parse_category_path(line_str))
                continue

            # Process review lines (fixing legacy 'cutomer:' typo)
            if collecting_reviews:
                review_match = re.search(
                    r"(\d{4}-\d{1,2}-\d{1,2})\s+cutomer:\s*(\S+)\s+rating:\s*(\d+)\s+votes:\s*(\d+)\s+helpful:\s*(\d+)",
                    line_str,
                )
                if review_match:
                    raw_date, customer_id, rating, votes, helpful = (
                        review_match.groups()
                    )
                    # Standardize date to YYYY-MM-DD
                    date_iso = datetime.strptime(raw_date, "%Y-%m-%d").strftime(
                        "%Y-%m-%d"
                    )
                    current_item["reviews"].append(
                        {
                            "date": date_iso,
                            "customer_id": customer_id,
                            "rating": int(rating),
                            "votes": int(votes),
                            "helpful": int(helpful),
                        }
                    )

        # Flush final record
        if current_item and not current_item.get("discontinued", False):
            yield current_item


def run_pipeline():
    record_count = 0
    with open(OUTPUT_FILE_PATH, "w", encoding="utf-8") as out_f:
        for record in parse_amazon_meta(RAW_FILE_PATH):
            record.pop("discontinued", None)
            out_f.write(json.dumps(record) + "\n")
            record_count += 1
    print(f"Pipeline complete. Processed and wrote {record_count} valid records.")


if __name__ == "__main__":
    run_pipeline()

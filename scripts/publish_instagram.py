import json
import os
import time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
LATEST_FILE = ROOT / "docs" / "latest.json"


def api_post(base_url: str, path: str, payload: dict) -> dict:
    r = requests.post(f"{base_url}/{path}", data=payload, timeout=30)
    data = r.json()
    if r.status_code >= 400 or "error" in data:
        raise RuntimeError(f"Instagram API error on {path}: {data}")
    return data


def main():
    token = os.environ["IG_ACCESS_TOKEN"].strip()
    ig_user_id = os.environ["IG_USER_ID"].strip()
    pages_base = os.environ["PAGES_BASE_URL"].rstrip("/")

    # Support both graph.instagram.com (IGAA/IGA tokens) and graph.facebook.com (EAA tokens)
    base_url = "https://graph.instagram.com/v22.0" if token.startswith("IG") else "https://graph.facebook.com/v22.0"

    meta = json.loads(LATEST_FILE.read_text(encoding="utf-8"))
    folder = meta["folder"]
    caption = meta["caption"]

    # 1. Create child media containers for each of the 6 slides
    child_ids = []
    for fname in meta["slides"]:
        image_url = f"{pages_base}/{folder}/{fname}"
        print("Creating container for:", image_url)
        res = api_post(base_url, f"{ig_user_id}/media", {
            "image_url": image_url,
            "is_carousel_item": "true",
            "access_token": token,
        })
        child_ids.append(res["id"])
        time.sleep(1.5)

    # 2. Create parent carousel container
    parent = api_post(base_url, f"{ig_user_id}/media", {
        "media_type": "CAROUSEL",
        "children": ",".join(child_ids),
        "caption": caption,
        "access_token": token,
    })
    creation_id = parent["id"]
    print("Carousel container created:", creation_id)
    time.sleep(5)

    # 3. Publish carousel to @jasmin.ver_1.0!
    published = api_post(base_url, f"{ig_user_id}/media_publish", {
        "creation_id": creation_id,
        "access_token": token,
    })
    print("PUBLISHED TO @jasmin.ver_1.0! Media ID:", published["id"])


if __name__ == "__main__":
    main()

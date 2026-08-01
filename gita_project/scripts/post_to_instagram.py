"""
Publishes the carousel described in data/run_meta.json to Instagram.

Requires the two slide images to already be pushed to a PUBLIC GitHub repo
(Instagram's API fetches images from a public URL - it cannot accept raw
file uploads). The GitHub Actions workflow handles the git push step before
this script runs.

Required environment variables:
    IG_USER_ID        - your Instagram Business Account ID
    IG_ACCESS_TOKEN   - long-lived Graph API access token
    GITHUB_REPOSITORY - "owner/repo" (auto-set by GitHub Actions)
    GITHUB_REF_NAME    - branch name, e.g. "main" (auto-set by GitHub Actions)
"""

import json
import os
import sys
import time
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META_PATH = os.path.join(BASE_DIR, "data", "run_meta.json")

GRAPH_API = "https://graph.facebook.com/v21.0"


def raw_url(repo, branch, relative_path):
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{relative_path}"


def create_carousel_item(ig_user_id, token, image_url):
    resp = requests.post(
        f"{GRAPH_API}/{ig_user_id}/media",
        data={
            "image_url": image_url,
            "is_carousel_item": "true",
            "access_token": token,
        },
    )
    resp.raise_for_status()
    return resp.json()["id"]


def wait_until_ready(container_id, token, timeout=60):
    """Poll a media container until Meta finishes processing it."""
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(
            f"{GRAPH_API}/{container_id}",
            params={"fields": "status_code", "access_token": token},
        )
        resp.raise_for_status()
        status = resp.json().get("status_code")
        if status == "FINISHED":
            return True
        if status == "ERROR":
            raise RuntimeError(f"Container {container_id} failed processing")
        time.sleep(3)
    raise TimeoutError(f"Container {container_id} did not finish in time")


def create_carousel_container(ig_user_id, token, children_ids, caption):
    resp = requests.post(
        f"{GRAPH_API}/{ig_user_id}/media",
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(children_ids),
            "caption": caption,
            "access_token": token,
        },
    )
    resp.raise_for_status()
    return resp.json()["id"]


def publish(ig_user_id, token, creation_id):
    resp = requests.post(
        f"{GRAPH_API}/{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": token},
    )
    resp.raise_for_status()
    return resp.json()


def main():
    ig_user_id = os.environ["IG_USER_ID"]
    token = os.environ["IG_ACCESS_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    branch = os.environ.get("GITHUB_REF_NAME", "main")

    with open(META_PATH, encoding="utf-8") as f:
        meta = json.load(f)

    url1 = raw_url(repo, branch, meta["slide1_file"])
    url2 = raw_url(repo, branch, meta["slide2_file"])
    print(f"Slide 1 URL: {url1}")
    print(f"Slide 2 URL: {url2}")

    item1 = create_carousel_item(ig_user_id, token, url1)
    item2 = create_carousel_item(ig_user_id, token, url2)
    print(f"Created carousel items: {item1}, {item2}")

    wait_until_ready(item1, token)
    wait_until_ready(item2, token)

    carousel_id = create_carousel_container(ig_user_id, token, [item1, item2], meta["caption"])
    print(f"Created carousel container: {carousel_id}")

    wait_until_ready(carousel_id, token)

    result = publish(ig_user_id, token, carousel_id)
    print(f"Published! Media ID: {result.get('id')}")


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
        print(f"Graph API error: {e.response.text}", file=sys.stderr)
        sys.exit(1)

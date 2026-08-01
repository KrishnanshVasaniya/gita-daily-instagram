# Daily Bhagavad Gita Instagram Automation

Posts one verse a day as a 2-slide carousel (Sanskrit + English on slide 1,
short explanation on slide 2) to Instagram, fully automated via GitHub Actions.

---

## How it works

1. `scripts/daily_post.py` picks the next verse from `data/verses.json` (in
   order, tracked by `data/state.json`) and generates its carousel images
   into `output/`.
2. GitHub Actions commits those new images to the repo.
3. `scripts/post_to_instagram.py` calls the Instagram Graph API, pointing it
   at the images' `raw.githubusercontent.com` URLs, and publishes the post.
4. This repeats daily on a schedule (default: 9:00 AM IST) — no manual work.

---

## One-time setup

### 1. Instagram + Facebook

1. Create the new Instagram account.
2. In the app: **Settings → Account type and tools → Switch to professional
   account** → choose **Creator** or **Business**.
3. Create a Facebook Page (any name, doesn't need followers) if you don't
   have one, and link it to the Instagram account during that same setup
   flow (or via Settings → Linked accounts).

### 2. Meta Developer App

1. Go to **developers.facebook.com** → **My Apps** → **Create App** → type
   **Business**.
2. Add the **Instagram Graph API** product to the app.
3. Under **Tools → Graph API Explorer**:
   - Select your app.
   - Request these permissions: `instagram_basic`, `instagram_content_publish`,
     `pages_show_list`, `pages_read_engagement`.
   - Generate a **User Access Token**.
4. Exchange it for a **long-lived token** (lasts ~60 days) — either via the
   Access Token Debugger's "Extend Access Token" button, or:
   ```
   GET https://graph.facebook.com/v21.0/oauth/access_token
       ?grant_type=fb_exchange_token
       &client_id={app-id}
       &client_secret={app-secret}
       &fb_exchange_token={short-lived-token}
   ```
5. Get your **Instagram Business Account ID**:
   ```
   GET https://graph.facebook.com/v21.0/me/accounts?access_token={token}
   ```
   → take the Page ID from the result, then:
   ```
   GET https://graph.facebook.com/v21.0/{page-id}?fields=instagram_business_account&access_token={token}
   ```
   → this gives you the `IG_USER_ID`.

> **Token expiry:** long-lived tokens expire after ~60 days. Set yourself a
> reminder to refresh it (`GET /refresh_access_token?grant_type=ig_refresh_token`)
> before then, or ask me to build an automated refresh workflow.

### 3. GitHub repo

1. Push this project to a **public** GitHub repo (public is required so
   `raw.githubusercontent.com` URLs are fetchable by Instagram — if you'd
   rather keep it private, ask me about the GitHub Pages alternative).
2. In the repo: **Settings → Secrets and variables → Actions → New repository
   secret**, add:
   - `IG_USER_ID` — from step 2.5 above
   - `IG_ACCESS_TOKEN` — your long-lived token
3. That's it — the workflow in `.github/workflows/daily_post.yml` will run
   on schedule automatically once these secrets exist.

---

## Verse content

`data/verses.json` holds the complete Gita — **701 entries covering all 18
chapters** — and the poster works through them in order, looping back to the
start once it reaches the end.

It is **generated output**. Do not edit it by hand; edits are overwritten on
the next build. It is produced from two sources:

| Source | What it holds |
| --- | --- |
| `data/authoritative.json` | Sanskrit (Devanagari + transliteration) for all 701 verses, from the [gita/gita](https://github.com/gita/gita) dataset |
| `chapter_content/ch1.py` … `ch18.py` | The original English translation and explanation for each verse |

Each chapter module defines a single dict keyed by verse number:

```python
CONTENT = {
    47: {
        "t": "Your right is to action alone, never to its fruits. ...",
        "e": "The most quoted verse in the Gita, and the closing line ...",
    },
}
```

To revise a verse, edit its `"t"` or `"e"` in the relevant chapter module and
rebuild:

```bash
python scripts/merge_verses.py
```

The build is idempotent — every chapter is regenerated on each run, so it is
safe to run repeatedly. It pairs each entry with its Sanskrit, normalises the
verse marker to the `॥४७॥` form, and refuses to write anything if a verse is
missing content or a module names a verse that does not exist in the dataset.

> **Verse numbering** follows `authoritative.json` throughout. That recension
> gives Chapter 13 thirty-five verses (some editions have thirty-four), for a
> total of 701 rather than the commonly cited 700.

---

## Testing locally (optional)

```bash
pip install -r requirements.txt
python scripts/merge_verses.py       # rebuild data/verses.json from source
cd scripts
python daily_post.py                 # generates next verse's images
python generate_card.py --chapter 2 --verse 47   # generate one verse on demand
```

`post_to_instagram.py` requires `GITHUB_REPOSITORY` and `GITHUB_REF_NAME`,
which GitHub Actions sets automatically — it's not meant to be run locally
unless you export those manually.

---

## Posting twice a day

Add a second `cron` line under `on: schedule:` in
`.github/workflows/daily_post.yml`, e.g. `"30 12 * * *"` for a ~6:00 PM IST
second post.

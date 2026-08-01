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

## Adding more verses

`data/verses.json` currently ships with 7 sample verses. Add more entries in
the same shape:

```json
{
  "chapter": 2,
  "verse": 47,
  "sanskrit": "...",
  "translation": "...",
  "explanation": "..."
}
```

The poster works through the list in order and loops back to the start once
it reaches the end — so the list can grow over time without breaking
anything. I'm happy to help draft the remaining verses in batches whenever
you're ready (all 700 is a big batch — doing it in chunks, say by chapter,
keeps quality high).

---

## Testing locally (optional)

```bash
pip install -r requirements.txt
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

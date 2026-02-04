# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Development & Runtime Commands

### Environment setup
- From the project root (this directory):
  - Create and activate a virtualenv, install deps, and set up Playwright (from `docs/README.md`):
    - `python3 -m venv .venv`
    - `source .venv/bin/activate`
    - `pip install -r requirements.txt`
    - `playwright install chromium`
  - One-shot installer that also creates `config.json` from `config.example.json` and initializes git if needed: `./setup.sh`

### Core data collection flows
There are two main collection pipelines; both write to `data/all_data.json` and can push to git:

- **HTTP API–based collectors (preferred for scripted runs)**
  - Entry point: `python3 main.py`
  - Uses `collectors/` + `models.py` + `utils/` (cookie validation/refresh + notifications) to pull data via platform APIs.
  - Respects per-platform `enabled` flags and cookies in `config.json` and can auto-refresh cookies interactively when expired.

- **Playwright/headless-browser collectors (used by launchd jobs, richer per-work metrics)**
  - Entry point: `python3 collect_all.py`
  - Requires Playwright Chromium installed (see setup above).
  - Runs headless Chromium, injects cookies from `config.json`, intercepts API responses, and appends CSV exports to:
    - `data/accounts.csv`, `data/works.csv`, `data/daily_snapshots.csv`.
  - Can auto-open a non-headless browser window for 视频号 login when cookies are invalid and then persist new cookies back into `config.json`.

### Cookie and session management
- **Sync cookies directly from a logged-in browser** (Chrome by default, see script for other browsers):
  - `python3 sync_cookie_from_browser.py`
  - Optional flags:
    - `-b chrome|chromium|edge|firefox|safari`
    - `-p douyin -p xiaohongshu -p shipinhao` (limit to specific platforms)
    - `--no-validate` (skip post-sync validation).
  - Updates `config.json` (or creates it from `config.example.json`) and can immediately validate cookies using `utils.cookie_validator`.

- **Interactive cookie guidance** (manual copy/paste from devtools):
  - `python3 get_cookie.py` (menu) or `python3 get_cookie.py douyin` / `xiaohongshu` / `shipinhao`.

- **Keep sessions alive with periodic background browsing** (Playwright-based):
  - Long-running service: `python3 utils/session_keeper.py`
  - Uses `config.json` cookies to periodically hit creator dashboards for 抖音/小红书/视频号 and delay cookie expiry.

- **Explicit cookie validation/debugging**:
  - Validate current cookies against each platform’s auth endpoints and print statuses: `python3 utils/cookie_validator.py`.
  - Cookie auto-refresh logic (opened via `main.py` and helper scripts) is implemented in `utils/cookie_refresher.py`; you generally don’t call it directly.

### Scheduling / automation
- **Interactive launchd setup for `main.py` (Mac)**
  - `python3 setup_cron.py`
  - Generates a `LaunchAgents` plist referencing `main.py`, lets you choose daily run time, and manages `logs/collect.log` / `logs/collect.error.log`.

- **Predefined launchd job for `collect_all.py` (Mac)**
  - Install/uninstall a fixed schedule (currently daily at 09:00 and 21:00) using the existing `com.creator.datacollector.plist`:
    - `./setup_schedule.sh`
  - Common manual commands echoed by the script:
    - Run once now: `python3 collect_all.py`
    - Check status: `launchctl list | grep creator`

### Chrome extension & Native Messaging
- Load the extension in Chrome for interactive per-page collection:
  - Go to `chrome://extensions`, enable **Developer mode**, choose **Load unpacked**, and select the `chrome-extension` directory (see `chrome-extension/README.md`).
- Install the Native Messaging host so the extension can update `config.json` cookies via `native_host/cookie_sync_host.py`:
  - `./setup_native_host.sh <extension_id>` (or run without args to be guided; the script will write `native_host/com.creator.datacollector.json` and copy it into the browser-specific NativeMessagingHosts directories).

### Data export and debugging
- Export the current `data/all_data.json` into CSVs for analysis (account, works, and daily snapshots):
  - `python3 export_csv.py`
- Directly debug platform APIs using the cookies in `config.json`:
  - `python3 debug_api.py` (hits representative Douyin/Xiaohongshu/视频号 endpoints and prints truncated JSON).
- One-time login bootstrap for 小红书 Playwright sessions (persistent Chromium profile):
  - `python3 login_xiaohongshu.py` (opens a non-headless window and saves session state under `~/.creator-data-tracker/browser-data/xiaohongshu`).

### Dashboard / front-end
- Local preview of the dashboard (static front-end, no build step):
  - `open index.html` or `open dashboard.html` (on macOS), or open those files in a browser.
- Production dashboard is deployed separately (per `docs/README.md`) at `https://creator-data-tracker.vercel.app/` and consumes the same `data/all_data.json` schema.

## Architecture Overview

### High-level system
- The system tracks creator metrics for 抖音 (`douyin`), 小红书 (`xiaohongshu`), and 视频号 (`shipinhao`), collecting both account-level aggregates and per-work statistics.
- **Configuration** lives in `config.json` (template: `config.example.json`):
  - Per-platform sections with `enabled`, `cookie`, and metadata like `cookie_updated_at`, `cookie_source`, and optional `user_id` for certain flows.
  - A `settings` section controlling things like `auto_push_to_github` and notification backends.
- **Collected data** is persisted in `data/all_data.json` using the structured schema from `models.py` and is the single source of truth for both the HTML dashboard and CSV exports.

### Data model layer (`models.py`)
- Central dataclasses:
  - `WorkData`: normalized representation of a single post/video across platforms (IDs, title, timestamps, views/likes/comments/shares/collects, plus extended fields such as `impressions`, `click_rate`, `avg_view_time`, `new_followers`).
  - `AccountData`: per-platform aggregate metrics (followers, total views/likes/works, avatar URL, total impressions/collects).
  - `PlatformData`: groups one `AccountData` with a list of `WorkData` for a single platform.
  - `DailySnapshot`: compact per-day-per-platform rollups (current totals + daily deltas for followers, views, likes, impressions, collects).
  - `AllPlatformData`: top-level aggregate with optional `douyin`, `xiaohongshu`, `shipinhao` `PlatformData` plus a list of `DailySnapshot` entries.
- `AllPlatformData.save/load` are the canonical helpers for reading/writing `data/all_data.json` in the typed shape that collectors and the dashboard expect.
- When changing any of these dataclasses, you must also review:
  - `main.py` (daily delta computation and snapshot pruning),
  - `collect_all.py` and `export_csv.py` (CSV column layout and JSON field expectations),
  - front-end code in `index.html` / `dashboard.html` that reads `all_data.json`.

### Collector layer (`collectors/` + `main.py` + `collect_all.py`)
- **Abstract base**: `collectors/base.py` defines `BaseCollector`:
  - Wraps a configured `requests.Session` with a common UA + `Cookie` header.
  - Provides `_request` with backoff/logging and `collect_all` that orchestrates `collect_account_info` + `collect_works`, computes derived totals/impressions, and returns a `PlatformData` instance.
  - Integrates `utils.cookie_validator.CookieValidator` in `collect_all_with_validation` to proactively fail fast on invalid cookies and optionally notify via `NotificationManager`.

- **Platform-specific collectors** (HTTP API based):
  - `collectors/douyin.py`:
    - Hits Douyin creator APIs for user info and paginated `aweme` lists.
    - Maps API responses into `AccountData` (nickname, uid, follower counts, total likes, avatar) and `WorkData` (per-aweme stats, share/collect counts, URLs).
  - `collectors/xiaohongshu.py`:
    - Hybrid strategy: creator-API account info + Playwright-based note analysis API interception + public-profile HTML scraping as a fallback.
    - Populates extended metrics like exposures (`impressions`), cover click rate, average view time, and new followers per note.
  - `collectors/shipinhao.py`:
    - Calls 视频号助手 APIs for auth data and paginated post lists.
    - Title and cover handling is defensive, supporting both structured `desc` objects and plain strings, and builds `WorkData` with read/like/comment/share/collect counts.

- **Main orchestrators**:
  - `main.py` (requests-based pipeline):
    - Loads `config.json`, constructs a `NotificationManager` and `CookieRefresher`.
    - Pre-validates cookies across platforms using `check_all_cookies` and, on expiration, calls `CookieRefresher.ensure_valid_cookie` to drive interactive browser logins and in-memory config updates (with persistent changes handled by helpers in `utils`).
    - Uses `collect_platform_data` to instantiate the appropriate collector class and aggregates results into an `AllPlatformData` instance, preserving and extending `daily_snapshots`.
    - Computes per-day deltas (`calculate_daily_change`) and prunes snapshots older than 90 days.
    - Writes the updated `all_data.json` and, if `settings.auto_push_to_github` is true, stages `data/` and `index.html`, commits, and pushes via subprocess git commands.

  - `collect_all.py` (Playwright-based pipeline):
    - Manually drives Chromium through creator dashboards for each platform, injecting cookies and intercepting network responses to reconstruct account/work data structures similar to `models.py` (but stored as plain dicts).
    - Contains platform-specific collectors (`collect_douyin`, `collect_xiaohongshu`, `collect_shipinhao`) that mirror the responsibilities of the HTTP collectors but using browser APIs (including auto-handling 视频号 login with a non-headless browser when needed and persisting refreshed cookies to `config.json`).
    - Maintains its own `daily_snapshots` structure compatible with the dashboard and CSV export and enforces a 90-day retention policy.
    - Appends CSV-friendly views of account/work/snapshot data for external tools and can perform git push when `settings.auto_push_to_github` is enabled.

- **Utility scripts tightly coupled to collectors**:
  - `debug_api.py`: low-level inspection of platform API responses using the same cookies; helpful when API contracts change.
  - `login_xiaohongshu.py`: prepares a persistent Playwright context for 小红书 that other flows can rely on.

### Cookie/session infrastructure (`utils/`, `native_host/`, `chrome-extension/`)
- **Validation and lifecycle** (`utils/`):
  - `cookie_validator.py` centralizes platform-specific validation endpoints, success predicates, and error code mappings, and exposes:
    - `CookieValidator.validate()` for per-cookie status,
    - `check_all_cookies(config)` and `check_cookie_expiry_warning(config)` for bulk checks and “about to expire” heuristics based on `cookie_updated_at` and per-platform expected lifetimes.
  - `cookie_refresher.py` encapsulates:
    - Opening the appropriate login URL in a real browser (preferring Chrome on macOS),
    - Reading cookies via `browser_cookie3`,
    - Persisting them back into `config.json`, and
    - Integrating with `cookie_validator` to confirm validity before accepting an update.
  - `session_keeper.py` runs a long-lived Playwright-based “keepalive” service that periodically visits creator dashboards with existing cookies, performs light scrolling, and detects when sessions begin redirecting to login, signalling that manual refresh is needed.
  - `notifier.py` implements multiple notification backends (macOS notifications, 企业微信机器人, DingTalk robot) and `NotificationManager`, which is wired into `main.py` and cookie utilities to surface cookie expiry, warnings, and collection success/failure.

- **Chrome extension integration**:
  - `chrome-extension/` is a standalone Chrome extension that:
    - Injects `content/*.js` into platform creator pages to intercept fetch/XHR responses or scrape DOM as a fallback.
    - Aggregates the same kinds of account/works metrics as the Python collectors and provides UI buttons for “采集当前页面” and JSON export, as described in `chrome-extension/README.md`.
  - `native_host/cookie_sync_host.py` implements a Chrome Native Messaging host that:
    - Listens for messages (e.g., `updateCookie`, `getConfig`) from the extension over stdin/stdout,
    - Updates `config.json` with new cookies (tracking `cookie_source="chrome_extension"` and per-platform `cookie_expires_hint`), and
    - Logs to `data/cookie_sync.log`.
  - `setup_native_host.sh` generates the Native Messaging manifest and installs it into the per-browser `NativeMessagingHosts` directories so Chrome/Chromium/Edge can talk to the Python host.

### Dashboard & reporting
- The front-end (see `docs/README.md` and `dashboard.html`/`index.html`) is a static HTML + JavaScript + Chart.js application that:
  - Reads `data/all_data.json` at load time,
  - Renders cross-platform comparisons, per-platform time series based on `daily_snapshots`, and TOP 5 works lists,
  - Supports date-range filters (7 days / 30 days / all) driven by the snapshot timestamps.
- CSV outputs generated by `collect_all.py` and `export_csv.py` mirror the same schema, enabling external BI tooling without duplicating aggregation logic.

### Scheduling & automation artifacts
- `com.creator.datacollector.plist` and `setup_schedule.sh` tie the Playwright-based `collect_all.py` into macOS `launchd` for twice-daily runs and log to `data/launchd.log`.
- `setup_cron.py` dynamically generates a `LaunchAgents` plist targeting `main.py` and keeps logs under `logs/`.
- `com.creator.sessionkeeper.plist` (if enabled on the host system) can be used to keep `utils/session_keeper.py` running under `launchd`, ensuring creator sessions stay warm between automated collection runs.

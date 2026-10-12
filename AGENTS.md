## Cursor Cloud specific instructions

The portal is an Astro 5 static site. `landing/` is a separate Astro hub, and `webhook/` is an optional Express server. Cloudflare builds pin Node 24 (`.node-version`, `.github/workflows/deploy.yml`). On a Cloud Agent VM, `node` on the default `PATH` is Node 22 at `/exec-daemon/node`, which hides `/usr/local/bin`.

Install (safe to run twice):

```bash
export PATH="/usr/local/bin:$PATH"
if ! /usr/local/bin/node -v 2>/dev/null | grep -q '^v24\.'; then
  curl -fsSL https://nodejs.org/dist/v24.21.0/node-v24.21.0-linux-x64.tar.xz | sudo tar -xJ -C /usr/local --strip-components=1 --no-same-owner
fi
npm ci --prefer-offline --no-audit --no-fund
npm ci --prefix landing --prefer-offline --no-audit --no-fund
npm ci --prefix webhook --prefer-offline --no-audit --no-fund
```

Start the portal (foreground):

```bash
export PATH="/usr/local/bin:$PATH"
sudo sysctl -w fs.inotify.max_user_watches=1048576 fs.inotify.max_user_instances=1024
unset BUILD_LANGS
npm run dev
```

The dev server listens on http://127.0.0.1:4321.

- The checkout contains on the order of 64k directories (`src/data`, `public`, `wappen/.vendor`). The VM's default inotify watch limit is too low, so `astro dev` logs `ENOSPC: System limit for number of file watchers reached` and can then abort with a JavaScript heap out-of-memory error. Raise the sysctl above before starting the dev server.
- Leave `BUILD_LANGS` unset for local dev. Prefixed locales respond: `/en/`, `/fr/`, `/cs/`, `/nl/`. `http://127.0.0.1:4321/` returns the site 404 page, because `[...locale]` static paths omit the default German locale and there is no separate root page. A production language build sets `BUILD_LANGS` to one code and uses `NODE_OPTIONS=--max-old-space-size=8192` (see the deploy workflow). Checking the dev server does not require that build.
- Landing: from `landing/`, `npm run dev -- --host 127.0.0.1 --port 4322` (http://127.0.0.1:4322/).
- Webhook: from `webhook/`, `npm start` listens on port 3456. `GET /health` works without secrets. `LEMONSQUEEZY_WEBHOOK_SECRET` and `MAILERLITE_API_KEY` are only needed for signed webhooks and newsletter delivery. `nodemailer` is imported when present and is not a dependency in `webhook/package.json`.

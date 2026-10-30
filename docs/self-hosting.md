# Private deployment

Adrian's running instance uses **https://sleep.apetre.sc/** on Newton, through its existing OrbStack Docker engine and shared Traefik proxy. Normal DNS points to Newton's private Tailscale IPv4 address. The container publishes no host port. Its Traefik router accepts loopback, Tailscale and private LAN source addresses; it does not trust a caller-supplied `X-Forwarded-For` header.

OrbStack translates forwarded connections to the `edge` network's gateway address before Traefik sees them. The source allowlist therefore supplements the private network perimeter; it cannot identify the original remote client on this Mac. The privacy boundary is the Tailscale-only DNS target and the Mac's private LAN/Tailscale ingress. Keep the shared proxy off public port forwards; use authentication or a separately restricted ingress if that deployment model changes.

The Mac must be awake with OrbStack and Tailscale running. OrbStack is already configured to start at login; the service uses `restart: unless-stopped`. This is persistent self-hosting on the Mac, not a cloud service that stays available while the Mac is asleep.

## Files and ownership

- Repository: `~/src/personal/pokemon-sleep-field-notes`, with this fork as `origin` and David Chen's repository as `upstream`.
- Persistent sanitized collection: `~/.local/share/pokemon-sleep-field-notes/collection/`. It contains `roster.json`, `inventory.json`, `history.json` and `snapshots/`.
- `.env` selects `SLEEP_DATA_DIR` and optionally `SLEEP_DOMAIN`. It is ignored by Git.
- Existing shared proxy: `~/src/traefik/docker-compose.yml`, external Docker network `edge`.
- Host certificate/key: `~/src/traefik/certs/pokemon-sleep/`; certificate configuration: `~/src/traefik/dynamic/tls-pokemon-sleep.yml`.

The code repository retains the upstream's fictional demo for tests and portable previews. Actual account snapshots stay outside Git. The Docker context is an allowlist of HTML, CSS, JavaScript, artwork and server files. Collection JSON, scripts, private working files, native binaries and CA keys are excluded from the image. NGINX runs as its unprivileged image user with a read-only root filesystem and read-only collection mount.

## Start or update the web service

Requirements: Docker Compose, the existing `edge` network/proxy, and a complete sanitized collection. From the repository root, create `.env` with an absolute local path:

```dotenv
SLEEP_DATA_DIR=/Users/YOUR_USER/.local/share/pokemon-sleep-field-notes/collection
SLEEP_DOMAIN=sleep.apetre.sc
```

Then run:

```sh
docker --context orbstack compose config --quiet
docker --context orbstack compose up -d --build --wait
docker --context orbstack compose ps
```

The service refuses to start without all three export files and the snapshots directory. It serves only static files and the explicitly mapped sanitized JSON paths. Root `/` redirects to `/pokemon-sleep/`. Latest export JSON is revalidated; content-addressed snapshots can be cached immutably.

`docker compose down` removes the service, not the bind-mounted collection. Recreating the container or rebuilding the image preserves the account data. No named volume contains the only copy.

## DNS and TLS

The `apetre.sc` zone is hosted in Route 53. The deployment adds a single `A` record for `sleep.apetre.sc` with a private Tailscale address and a 300-second TTL. It is separate from the homelab's automatically discovered public Swarm hostnames; do not point this record at `home.apetre.sc`.

Use Tailscale on a client to reach the normal DNS target. A LAN-only client can use a local DNS/hosts override to Newton's LAN address for the same hostname. DNS does not install a route to Tailscale addresses on devices outside the tailnet.

TLS uses Newton's existing **mkcert CA**, matching the other local Traefik services. A client must trust that same CA. The server certificate covers only `sleep.apetre.sc`; the mkcert root private key remains on the Mac, outside the repository and container. Add a separate SNI certificate configuration under the shared proxy's `dynamic/` directory; do not replace another project's certificate or the default TLS store. No public ACME challenge or Internet exposure is required.

## Refresh the collection

The web container never logs in to Pokémon Sleep or captures phone traffic. Obtain a new owner-authorized full decoded response using the established private capture procedure. Keep its captures, raw response, credentials and CA outside this repository and outside `SLEEP_DATA_DIR`.

Import directly to the persistent sanitized directory:

```sh
python3 scripts/sync_sleep_collection.py \
  --workspace /absolute/private/workspace \
  --source /absolute/private/full-response.json \
  --captured-at YYYY-MM-DD \
  --output-root /absolute/path/to/pokemon-sleep-field-notes/collection
```

Use the actual capture date. The importer validates the paired exports in isolation, preserves history, writes the immutable paired snapshot, and publishes the history manifest last. A failed import preserves the last working collection. Do not rerun demo removal against this real runtime directory. New data is visible through the bind mount without rebuilding or restarting the web container.

The present ID mapping has known gaps for a few main skills and items; unresolved fields stay unresolved. Server Pokémon IDs and the private identity map are not published. See the research workspace's Field Notes setup notes for the original API verification and OCR comparison.

## Back up and restore

Back up the complete `collection/` directory, including `history.json` and `snapshots/`, with the rest of the Mac's personal data. Store backups outside Git and the web document root. Restore those files to the path selected in `.env`, then run `compose up -d --wait`. The deployment does not install a backup schedule or an automatic account refresh.

## Develop independently and check upstream

Changes belong on this fork's `main`. To inspect upstream improvements without replacing local work:

```sh
git fetch upstream
git log --oneline main..upstream/main
git diff main...upstream/main
```

Review and cherry-pick useful commits or make a deliberate merge, then rerun the README checks and rebuild the service. Do not force-reset this fork to upstream. No periodic check job is installed.

## Reference documentation

- [OrbStack networking](https://docs.orbstack.dev/docker/network)
- [Traefik IPAllowList](https://doc.traefik.io/traefik/reference/routing-configuration/http/middlewares/ipallowlist/)
- [Official unprivileged NGINX image](https://github.com/nginx/docker-nginx-unprivileged)

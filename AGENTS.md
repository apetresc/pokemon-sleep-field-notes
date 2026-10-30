# Adrian's Pokémon Sleep Field Notes

This is Adrian's independently developed fork. Read README.md and docs/self-hosting.md before deployment work. `origin` is apetresc/pokemon-sleep-field-notes; `upstream` is davidzlchen/pokemon-sleep-field-notes. Preserve upstream attribution and review upstream changes selectively.

The production instance is private through Tailscale/LAN. Collection data belongs outside Git in the directory selected by SLEEP_DATA_DIR; use the importer's --output-root option. Keep the checked-in fictional demo intact for tests. Never commit Adrian's actual roster, inventory, history, snapshots, credentials or private capture files. The Docker context is an allowlist, and the web container receives only sanitized runtime data, read-only. See docs/self-hosting.md for the live deployment and refresh workflow. No automatic game login or account capture is installed.

The original template setup guidance follows; completed setup steps do not need repeating for Adrian's existing instance.

Read README.md first. Work toward a verified local Field Notes site and, when the user
asks to publish, a repository and website owned by that user.

1. Clone/copy this template into a new directory. Preserve unrelated files.
2. Serve the included fictional demo with `python3 -m http.server 8765` and show
   `/pokemon-sleep/`. No installs are needed for this first step.
3. Ask only for the public display name, timezone, and data source. Run
   `scripts/configure.py`. Do not silently use David's identity or domain.
4. If the user supplies a decoded full response, follow docs/import.md. Otherwise
   explain docs/capture.md and its compatibility limit. Screenshots/manual entry
   are possible custom work, not a supported automated importer in this release.
5. Never guess missing fields or call captured updates a full roster. Check the
   reported count against the phone's box count when the user can supply it.
6. Keep raw data, captures, native client files, CA keys, and credentials outside
   the public repository or under ignored `.private/`. Never print their values,
   upload them to GitHub, or publish them through a web server. Serve the website
   only after private files are outside its document root. The root server is safe
   for a fresh demo clone only, before capture. Use docs/import.md's staging server
   after importing. `.gitignore` does not prevent HTTP file serving.
7. Obtain specific user authorization before configuring a phone proxy/trust,
   handling account credentials, or sending the optional full-data request.
   A request to build a site alone does not authorize these account/network steps.
   Do not clear data, transfer an account, change gameplay, or refresh/login
   independently. Never bypass the supported-client checks or retry an expired
   session in a loop. Let the owner relaunch the phone and supply a fresh capture.
8. Remove only the fictional demo with scripts/remove_demo.py. Import, run the
   documented tests, inspect public exports and share links, and verify desktop
   and mobile rendering. Do not publish the demo as the user's real collection.
9. Before creating/pushing a public repository, review all staged paths and scan
   for credentials/private identifiers. Preserve third-party attribution/NOTICE.
   If publishing is authorized, deploy only staged public site files; never
   point a static host at `.private/` or ship native client files.
10. No schedules are installed. If asked, determine a working private acquisition
    method first, keep its credentials out of hosted source, preserve the last
    successful snapshot, and disclose account/session failures accurately.

Do not claim fresh-account capture or one-prompt account access was tested when
only demo/offline/synthetic tests have passed. Report setup gates precisely.

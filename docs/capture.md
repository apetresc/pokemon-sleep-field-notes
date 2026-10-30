# Optional capture from your own phone (experimental)

The simplest supported input is an existing full decoded JSON response. If you
have none, an agent can help with the steps below. This requires your involvement
on the phone and specific consent for the proxy/certificate and optional request.
There is no official export integration here, and no account credentials should
be pasted into a chat, issue, README, or public repository.

The original implementation used a temporary local mitmproxy capture of the
owner's normal iPhone session. HTTPS interception exposed another encrypted
application layer. Offline inspection of the matching Android client's Unity
metadata/native library supplied the decoding/signing recipe. Normal gameplay
traffic contained incremental updates; a dedicated full-user-data request
returned the complete box. This is why merely opening every Pokémon in a browser
is not the import path.

## Compatibility prerequisite

The bundled decoder accepts only these exact Pokémon Sleep v3.8.2 Android files:

| File | SHA-256 |
| --- | --- |
| `global-metadata.dat` | `eb0028b16a37e12573d3c6db3872eecabce585ca469156816ae4299941e3a506` |
| ARM64 `libil2cpp.so` | `75fbee2fdf553321dd5b243723916fe4e0979897e3432fe1b48ffe1452ce5377` |

Obtain the matching files locally from a client you can access. The public
[RaenonX APK dumper](https://github.com/RaenonX-PokemonSleep/pokemon-sleep-apk-dumper)
was a research source for the original build. APK packaging/availability may
change. This repository does not distribute the APK, binaries, encryption
literals, or a general extractor. Put the matching files in `.private/`.
**Stop if hashes differ.** Do not disable checks or assume newer offsets work.
Fresh-account capture across arbitrary devices/versions has not been validated.

## Capture a normal startup

Use a local Python 3.12+ environment for the optional tools (the offline site
import itself needs only Python 3.11+):

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-capture.txt
```

Have the owner approve the temporary proxy/trust setup, then on the Mac/PC:

```sh
umask 077
mkdir -p .private/ca
.venv/bin/mitmdump --listen-host YOUR_PRIVATE_LAN_IP --listen-port 8080 \
  --allow-hosts '^api\.sleep\.pokemon\.co\.jp:443$' \
  --set confdir=.private/ca --set flow_detail=0 \
  --set 'save_stream_filter=~d ^api\.sleep\.pokemon\.co\.jp$' \
  -w .private/capture.flows
```

`allow_hosts` matches `hostname:port`, while the `~d` save filter matches the
hostname alone. Keep the `:443` in the interception pattern so HTTPS API traffic
is decrypted instead of being tunneled without inspection.

Replace the private LAN IP, keep the devices on the same trusted Wi-Fi, and keep
the proxy in a foreground terminal. Allow only the specific listener if the
firewall requires approval; do not disable the firewall. Check that the listener
is reachable before altering phone settings.

On the iPhone, the owner sets this network's **Configure Proxy → Manual** to that
IP and port, visits `http://mitm.it` to install the temporary local certificate,
and enables trust under **General → About → Certificate Trust Settings**. Follow
[mitmproxy's certificate instructions](https://docs.mitmproxy.org/stable/concepts/certificates/)
and [Apple's manual trust instructions](https://support.apple.com/en-us/102390).
Device passcodes are entered by the owner directly on the phone.

Close and relaunch Pokémon Sleep normally, then open the box. Stop the capture
with Ctrl+C. Do not clear game data or transfer/link/unlink an account. Captures
must include the normal token/login exchange and authenticated traffic; the
fetcher verifies signatures before preparing anything. Captures expire with the
session, so do the next step promptly. A session error requires a fresh normal
phone launch/capture, not automated login refresh.

**Always clean up:** set the phone's Wi-Fi proxy Off, remove the temporary
certificate profile/trust, stop the proxy, and verify the listener is closed.
Do this on failure as well as success, before changing networks. CA keys and
captures stay private. No game requests are recorded/published in this repository.

## Decode offline, then optionally fetch the full snapshot

```sh
.venv/bin/python scripts/decode_api_capture.py .private/capture.flows \
  --metadata .private/global-metadata.dat --native .private/libil2cpp.so \
  --output .private/decoded
```

This produces private decoded responses and a value-free summary. Its combined
`pokemon-wire-records.json` is **incremental updates only**, never a full import.
Inspect privately for a genuine `UD.pokemon.all` response. If absent, first verify
that a fresh captured session can prepare the fixed full-data request offline:

```sh
.venv/bin/python scripts/fetch_api_roster.py .private/capture.flows \
  --metadata .private/global-metadata.dat --native .private/libil2cpp.so \
  --output .private/full
```

That command sends nothing. With the owner's explicit authorization, repeat with
`--send` for one POST to `/api/common/get-all-ud`. This only requests data and has
no gameplay/account-transfer operations or automatic retries. It doesn't perform
login. Check `server_code: 0`, a successful decode, and a nonempty
`UD.pokemon.all`; HTTP 200 alone is not success. Error 1100 means session expired.
Unexpected/error responses are not imported. Proceed with `docs/import.md`, using
`.private/full/decoded.json` and the actual capture date.

These optional tools are derived from the original working session and covered
by synthetic cryptographic/request tests. A new user's live capture requires
its own verification; we have not claimed cross-account end-to-end validation.

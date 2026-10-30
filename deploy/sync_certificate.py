"""Copy one existing ACME wildcard from a read-only Docker volume; never log keys."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid

OPENSSL = os.environ.get('SLEEP_OPENSSL') or next(
    (str(path) for path in [Path('/opt/homebrew/opt/openssl@3/bin/openssl'),
                            Path('/usr/local/opt/openssl@3/bin/openssl')] if path.is_file()),
    shutil.which('openssl') or 'openssl')

READER_IMAGE = 'python:3.12-alpine@sha256:e6dae589c1c05976188fd3bd019afd091445fc533ed2ea29001beddc7368a9c8'
READER = '''import json,sys
data=json.load(open('/certs/acme.json'))
domain=sys.argv[1]
matches=[]
for resolver in data.values():
    for cert in resolver.get('Certificates',[]):
        names=[cert.get('domain',{}).get('main')]+(cert.get('domain',{}).get('sans') or [])
        if domain in names and '*.'+domain in names:
            matches.append(cert)
if len(matches)!=1:
    raise SystemExit('Expected exactly one matching wildcard certificate')
cert=matches[0]
print(json.dumps({'certificate':cert['certificate'],'key':cert['key']}))
'''


def command(args, *, data=None, timeout=30):
    result = subprocess.run(args, input=data, capture_output=True, timeout=timeout)
    if result.returncode:
        # stdout may contain a private key. Do not include captured output in errors.
        raise RuntimeError(f'{Path(args[0]).name} failed (exit {result.returncode})')
    return result.stdout


def read_bundle(context, volume, domain):
    payload = command([
        'docker', '--context', context, 'run', '--rm', '--network', 'none',
        '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true',
        '--mount', f'type=volume,source={volume},target=/certs,readonly',
        READER_IMAGE, 'python', '-B', '-c', READER, domain,
    ], timeout=180)
    decoded = json.loads(payload)
    return (base64.b64decode(decoded['certificate'], validate=True),
            base64.b64decode(decoded['key'], validate=True))


def install_bundle(certificate, key, output, hostname, reload_file=None):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    output.chmod(0o700)
    versions = output / 'versions'
    versions.mkdir(exist_ok=True, mode=0o700)
    staging = Path(tempfile.mkdtemp(prefix='.certificate-', dir=output))
    try:
        cert_path, key_path = staging / 'cert.pem', staging / 'key.pem'
        for path, content in [(cert_path, certificate), (key_path, key)]:
            path.touch(mode=0o600)
            path.write_bytes(content)
        # Refuse wrong-host, near-expiry, malformed or mismatched material before
        # replacing the working certificate. No key bytes go to logs or arguments.
        command([OPENSSL, 'verify', '-untrusted', str(cert_path),
                 '-verify_hostname', hostname, str(cert_path)])
        command([OPENSSL, 'x509', '-in', str(cert_path), '-noout', '-checkend', '604800'])
        cert_public = command([OPENSSL, 'x509', '-in', str(cert_path), '-pubkey', '-noout'])
        cert_public = command([OPENSSL, 'pkey', '-pubin', '-outform', 'DER'], data=cert_public)
        key_public = command([OPENSSL, 'pkey', '-in', str(key_path), '-pubout', '-outform', 'DER'])
        if cert_public != key_public:
            raise ValueError('Certificate and private key do not match')
        identifier = hashlib.sha256(certificate).hexdigest()
        current = output / 'current'
        if current.exists() and not current.is_symlink():
            raise ValueError('Refusing to replace a non-symlink certificate path')
        destination = f'versions/{identifier}'
        if current.is_symlink() and os.readlink(current) == destination:
            return {'status': 'unchanged', 'certificate_hash': identifier}
        release = versions / identifier
        if not release.exists():
            staging.rename(release)
        elif (release / 'cert.pem').read_bytes() != certificate or (release / 'key.pem').read_bytes() != key:
            raise ValueError('Existing certificate release differs')
        temporary_link = output / ('.current-' + uuid.uuid4().hex)
        temporary_link.symlink_to(destination)
        temporary_link.replace(current)
        if reload_file:
            Path(reload_file).touch()
        return {'status': 'updated', 'certificate_hash': identifier}
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--context', default='homelab')
    parser.add_argument('--volume', default='traefik_certs')
    parser.add_argument('--certificate-domain', default='apetre.sc')
    parser.add_argument('--hostname', default='sleep.apetre.sc')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reload-file', type=Path, required=True)
    args = parser.parse_args()
    try:
        certificate, key = read_bundle(args.context, args.volume, args.certificate_domain)
        print(json.dumps(install_bundle(certificate, key, args.output, args.hostname, args.reload_file)))
    except Exception as exc:
        # Keep launchd logs useful without rendering credentials or source JSON.
        parser.exit(1, f'Certificate sync failed ({type(exc).__name__}); last installed certificate preserved.\n')


if __name__ == '__main__':
    main()

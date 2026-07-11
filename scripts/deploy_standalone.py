"""Upload a local Next.js standalone build to DigitalOcean and restart PM2.

Avoids building on the droplet (which OOMs on small instances).

Usage:
    set DO_HOST=188.166.214.47
    set DO_USER=root
    set DO_PASSWORD=...
    python scripts/deploy_standalone.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = "/opt/quant-buffet"
STANDALONE = f"{APP_DIR}/.next/standalone"


def make_bundle() -> Path:
    standalone = ROOT / ".next" / "standalone"
    static = ROOT / ".next" / "static"
    public = ROOT / "public"
    if not (standalone / "server.js").is_file():
        raise SystemExit("Missing .next/standalone — run npm run build first.")
    if not static.is_dir():
        raise SystemExit("Missing .next/static — run npm run build first.")

    tmp = tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False)
    tmp.close()
    with tarfile.open(tmp.name, "w:gz") as tar:
        tar.add(standalone, arcname="standalone")
        tar.add(static, arcname="static")
        if public.is_dir():
            tar.add(public, arcname="public")
        eco = ROOT / "ecosystem.config.cjs"
        if eco.is_file():
            tar.add(eco, arcname="ecosystem.config.cjs")
        for msg in (ROOT / "messages").glob("*.json"):
            tar.add(msg, arcname=f"messages/{msg.name}")
    return Path(tmp.name)


def main() -> int:
    host = os.environ.get("DO_HOST", "188.166.214.47")
    user = os.environ.get("DO_USER", "root")
    password = os.environ.get("DO_PASSWORD")
    if not password:
        print("Set DO_PASSWORD.", file=sys.stderr)
        return 1

    print("Packaging standalone build…")
    tarball = make_bundle()
    size = tarball.stat().st_size
    print(f"Bundle size: {size:,} bytes")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {user}@{host}…")
    client.connect(host, username=user, password=password, timeout=90)
    sftp = client.open_sftp()

    remote_tar = "/tmp/quant-buffet-standalone.tar.gz"
    print("Uploading…")
    sftp.put(str(tarball), remote_tar)
    tarball.unlink(missing_ok=True)

    env_local = ROOT / ".env"
    if env_local.is_file():
        sftp.put(str(env_local), f"{APP_DIR}/.env")
    sftp.close()

    remote_script = f"""
set -e
mkdir -p {APP_DIR}/.next
rm -rf /tmp/qb-extract
mkdir -p /tmp/qb-extract
tar -xzf {remote_tar} -C /tmp/qb-extract
rm -f {remote_tar}
rm -rf {STANDALONE}
mv /tmp/qb-extract/standalone {STANDALONE}
mkdir -p {STANDALONE}/.next
rm -rf {STANDALONE}/.next/static
mv /tmp/qb-extract/static {STANDALONE}/.next/static
if [ -d /tmp/qb-extract/public ]; then
  rm -rf {STANDALONE}/public
  mv /tmp/qb-extract/public {STANDALONE}/public
fi
if [ -d /tmp/qb-extract/messages ]; then
  rm -rf {STANDALONE}/messages
  mv /tmp/qb-extract/messages {STANDALONE}/messages
fi
if [ -f /tmp/qb-extract/ecosystem.config.cjs ]; then
  cp /tmp/qb-extract/ecosystem.config.cjs {APP_DIR}/ecosystem.config.cjs
fi
rm -rf /tmp/qb-extract
if [ -f {APP_DIR}/.env ]; then
  sed -i 's|^DATABASE_URL=.*|DATABASE_URL="file:/var/lib/quant-buffet/dev.db"|' {APP_DIR}/.env
  sed -i 's|^AUTH_URL=.*|AUTH_URL="https://www.quantbuffet.com"|' {APP_DIR}/.env
  cp {APP_DIR}/.env {STANDALONE}/.env
fi
pm2 delete quant-buffet 2>/dev/null || true
pm2 start {APP_DIR}/ecosystem.config.cjs
pm2 save
curl -s -o /dev/null -w "%{{http_code}}" http://127.0.0.1:3088/en
echo
pm2 describe quant-buffet | head -20
"""
    print("Installing on server…")
    _, stdout, stderr = client.exec_command(remote_script, get_pty=True)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    # Avoid Windows console UnicodeEncodeError from progress glyphs
    sys.stdout.buffer.write(out.encode("utf-8", errors="replace"))
    sys.stdout.buffer.write(b"\n")
    if err.strip():
        sys.stderr.buffer.write(err.encode("utf-8", errors="replace"))
    client.close()
    return code


if __name__ == "__main__":
    raise SystemExit(main())

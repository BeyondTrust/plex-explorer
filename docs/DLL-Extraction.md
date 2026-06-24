# DLL Extraction

Pulls all DLLs from the worker directory through the plugin Custom API. Encodes each DLL as base64 via PowerShell, decodes locally.

## Usage

```bash
TOKEN=$(az account get-access-token --resource https://{ORG}.crm.dynamics.com --query accessToken -o tsv)
python3 tools/extract_dlls.py --org-url https://{ORG}.crm.dynamics.com --token "$TOKEN"
```

DLLs are saved to `./extracted_dlls/` by default. Use `--output-dir` to change the destination.

The worker directory is `C:\dataversesandboxworker` by default. Use `--worker-dir` to change it.

## How it works

1. Lists all `.dll` files in the worker directory via `CMD:dir /b *.dll`
2. For each DLL, reads it as base64 via `CMD:powershell -c "[Convert]::ToBase64String(...)"`
3. Decodes and saves locally
4. Prints progress as it goes

The full worker directory contains 216+ DLLs. Extraction takes a while since each DLL is base64-encoded through the plugin API.

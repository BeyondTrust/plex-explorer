# Plex Explorer - Tool Documentation

Step-by-step instructions for the tools included in this repo. Each tool builds on the previous one - the echo plugin gets you into the container, the C2 gives you a persistent shell, and from there you can deploy the gRPC probe and extract DLLs.

## Getting Started

You need a Dataverse environment with admin/system customizer privileges and the Azure CLI installed.

Get a token:

```bash
az login
az account get-access-token --resource https://{ORG}.crm.dynamics.com --query accessToken -o tsv
```

## Tools

| Tool | What it does | Guide |
|---|---|---|
| echo-plugin | Plugin that relays commands via cmd.exe | [[Echo Plugin]] |
| c2 | Blob storage command relay with web UI | [[C2]] |
| grpc-probe | Direct gRPC calls to the Plex sidecar | [[gRPC Probe]] |
| extract_dlls.py | Pull all DLLs off the container | [[DLL Extraction]] |

## Typical Workflow

1. Build and register the **echo plugin** in your Dataverse environment
2. Test it works with a simple `CMD:hostname` call
3. Set up the **C2** relay with an Azure Storage account
4. Deploy the C2 agent to the container
5. Use the C2 to deploy and run the **gRPC probe** against the sidecar
6. Use **extract_dlls.py** to pull the worker's DLLs for decompilation

Containers recycle roughly every 30 minutes. When this happens the C2 agent and any deployed tools are lost and need to be redeployed.

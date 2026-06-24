# Plex Explorer

A learning aid for security researchers explaining Microsoft's Dataverse plugin sandbox architecture, aka Plex.

Dataverse is the data layer behind Power Platform (Copilot Studio, Power Apps, Power Automate, etc.) and Dynamics 365. Customers extend it with plugins, custom .NET code triggered by data events like create or update. To stop untrusted third-party code from reaching the platform or other tenants, each plugin runs inside a sandbox: a .NET worker process in a Hyper-V isolated container. Microsoft runs these sandboxes at scale across Azure as part of the hosted Dataverse service. Plex is the internal name for the system that manages and executes them.

Presented at [Troopers 26](https://troopers.de/) by Simon Maxwell-Stewart ([BeyondTrust](https://x.com/btphantomlabs)).

**[Interactive Architecture Explorer](https://plex.btphantomlabs.com/)**


## Tools

- **[echo-plugin/](https://github.com/BeyondTrust/plex-explorer/blob/main/docs/Echo-Plugin.md)** - Minimal Dataverse Custom API plugin that relays commands via cmd.exe. The entry point into the sandbox container.
- **[c2/](https://github.com/BeyondTrust/plex-explorer/blob/main/docs/C2.md)** - Blob storage C2 relay. Operator console runs locally, PowerShell agent runs inside the container, commands pass through Azure Blob Storage.
- **[grpc-probe/](https://github.com/BeyondTrust/plex-explorer/blob/main/docs/gRPC-Probe.md)** - Go program that connects directly to the Plex sidecar gRPC service. Sends raw protobuf-encoded requests over a TLS channel.
- **[extract_dlls.py](https://github.com/BeyondTrust/plex-explorer/blob/main/docs/DLL-Extraction.md)** - Pulls all DLLs from the worker directory through the plugin Custom API.


## Other Files

- `openapi.yaml` - gRPC service definitions in OpenAPI format


## Prerequisites

1. A Dataverse environment with admin/system customizer privileges
2. Azure CLI (`az`) installed and logged in
3. An Azure Storage account (for the C2 relay)
4. Go 1.21+ (to build the gRPC probe, or use the pre-compiled release)


## Responsible Disclosure

All vulnerabilities found during this research were reported to Microsoft via MSRC
prior to public disclosure.

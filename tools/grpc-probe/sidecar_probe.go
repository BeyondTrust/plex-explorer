package main

import (
	"context"
	"crypto/tls"
	"flag"
	"fmt"
	"os"
	"strings"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"
	"google.golang.org/protobuf/proto"
)

const svcName = "Microsoft.PowerPlatform.Plex.SidecarContract.SidecarService"

// rawMsg wraps arbitrary bytes so grpc.Invoke can marshal/unmarshal
// without generated protobuf types.
type rawMsg struct{ data []byte }

func (m *rawMsg) ProtoReflect() proto.Message { return nil }
func (m *rawMsg) Reset()                       {}
func (m *rawMsg) String() string               { return "" }
func (m *rawMsg) ProtoMessage()                {}
func (m *rawMsg) Marshal() ([]byte, error)     { return m.data, nil }
func (m *rawMsg) Unmarshal(b []byte) error     { m.data = b; return nil }

// str encodes a string field in raw protobuf wire format (varint tag + length-delimited).
func str(field uint64, s string) []byte {
	data := []byte(s)
	tag := (field << 3) | 2
	var buf []byte
	for t := tag; ; {
		if t < 0x80 {
			buf = append(buf, byte(t))
			break
		}
		buf = append(buf, byte(t)|0x80)
		t >>= 7
	}
	l := uint64(len(data))
	for {
		if l < 0x80 {
			buf = append(buf, byte(l))
			break
		}
		buf = append(buf, byte(l)|0x80)
		l >>= 7
	}
	return append(buf, data...)
}

// call invokes a single gRPC method on the sidecar service and returns the raw response.
func call(conn *grpc.ClientConn, method string, req []byte) ([]byte, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	resp := &rawMsg{}
	err := conn.Invoke(ctx, "/"+svcName+"/"+method, &rawMsg{req}, resp)
	return resp.data, err
}

// parseFields decodes a flat protobuf message into field-number -> string values.
// Handles varint (wire type 0) and length-delimited (wire type 2) fields.
func parseFields(data []byte) map[uint64]string {
	result := make(map[uint64]string)
	i := 0
	for i < len(data) {
		tag := uint64(0)
		shift := uint(0)
		for i < len(data) {
			b := data[i]
			i++
			tag |= uint64(b&0x7f) << shift
			shift += 7
			if b < 0x80 {
				break
			}
		}
		field := tag >> 3
		wt := tag & 0x7
		switch wt {
		case 0:
			val := uint64(0)
			shift = 0
			for i < len(data) {
				b := data[i]
				i++
				val |= uint64(b&0x7f) << shift
				shift += 7
				if b < 0x80 {
					break
				}
			}
			result[field] = fmt.Sprintf("%d", val)
		case 2:
			length := uint64(0)
			shift = 0
			for i < len(data) {
				b := data[i]
				i++
				length |= uint64(b&0x7f) << shift
				shift += 7
				if b < 0x80 {
					break
				}
			}
			if i+int(length) <= len(data) {
				content := data[i : i+int(length)]
				i += int(length)
				s := string(content)
				if len(s) > 300 {
					s = s[:300] + "..."
				}
				result[field] = s
			}
		default:
			return result
		}
	}
	return result
}

func classifyError(err error) string {
	s := err.Error()
	if strings.Contains(s, "Unauthenticated") || strings.Contains(s, "PermissionDenied") {
		return "AUTH-GATED"
	}
	return "ERR"
}

func probeMethod(conn *grpc.ClientConn, name string, req []byte) {
	fmt.Printf("--- %s ---\n", name)
	resp, err := call(conn, name, req)
	if err != nil {
		fmt.Printf("  [%s] %v\n", classifyError(err), err)
	} else {
		fields := parseFields(resp)
		fmt.Printf("  [OK] %d bytes, fields=%v\n", len(resp), fields)
	}
}

func main() {
	target := flag.String("target", "", "Sidecar host:port (required)")
	tenantID := flag.String("tenant", "", "Azure AD tenant ID (required)")
	appID := flag.String("app", "", "Application/client ID (required)")
	resource := flag.String("resource", "https://graph.microsoft.com", "Token resource URL")
	flag.Parse()

	if *target == "" || *tenantID == "" || *appID == "" {
		fmt.Fprintf(os.Stderr, "Usage: sidecar_probe -target <host:port> -tenant <tenant-id> -app <app-id> [-resource <url>]\n")
		flag.PrintDefaults()
		os.Exit(1)
	}

	fmt.Printf("Sidecar Probe\n")
	fmt.Printf("  target:   %s\n", *target)
	fmt.Printf("  tenant:   %s\n", *tenantID)
	fmt.Printf("  app:      %s\n", *appID)
	fmt.Printf("  resource: %s\n\n", *resource)

	conn, err := grpc.Dial(*target,
		// InsecureSkipVerify is used here deliberately to allow for self-signed certs
		grpc.WithTransportCredentials(credentials.NewTLS(&tls.Config{InsecureSkipVerify: true})))
	if err != nil {
		fmt.Fprintf(os.Stderr, "dial failed: %v\n", err)
		os.Exit(1)
	}
	defer conn.Close()

	// GetAccessToken - request an OAuth token for the given tenant/app/resource
	fmt.Println("=== GetAccessToken ===")
	tokenReq := str(1, *resource)
	tokenReq = append(tokenReq, str(2, *tenantID)...)
	tokenReq = append(tokenReq, str(3, *appID)...)
	resp, err := call(conn, "GetAccessToken", tokenReq)
	if err != nil {
		fmt.Printf("  [%s] %v\n", classifyError(err), err)
	} else {
		fields := parseFields(resp)
		if tok, ok := fields[1]; ok && strings.HasPrefix(tok, "eyJ") {
			fmt.Printf("  [TOKEN] %s...\n", tok[:80])
		} else if errMsg, ok := fields[2]; ok {
			fmt.Printf("  [ERROR] %s\n", errMsg)
		} else {
			fmt.Printf("  [RESP] %d bytes, fields=%v\n", len(resp), fields)
		}
	}
	fmt.Println()

	// Probe additional sidecar methods with empty requests to test reachability
	probeMethod(conn, "GetEnvironmentVariables", []byte{})
	probeMethod(conn, "LoadExtensionPackage", []byte{})
	probeMethod(conn, "GetWorkerAssignedMetadata", []byte{})
	probeMethod(conn, "GetClusterEnvironmentSettings", []byte{})

	fmt.Println("\nDONE")
}

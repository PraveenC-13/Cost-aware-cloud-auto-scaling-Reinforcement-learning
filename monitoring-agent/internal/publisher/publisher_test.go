package publisher

import (
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/hkbk/monitoring-agent/internal/model"
)

func TestWrite_SendsCorrectLineProtocolAndHeaders(t *testing.T) {
	var capturedBody string
	var capturedAuth string
	var capturedQuery string

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		body, _ := io.ReadAll(r.Body)
		capturedBody = string(body)
		capturedAuth = r.Header.Get("Authorization")
		capturedQuery = r.URL.RawQuery
		w.WriteHeader(http.StatusNoContent)
	}))
	defer server.Close()

	p := New(server.URL, "hkbk", "autoscaler", "test-token-123")

	metric := model.Metric{
		Container:  "sample-app",
		CPUPercent: 42.5,
		MemPercent: 60.1,
		Timestamp:  time.Unix(0, 1700000000000000000),
	}

	if err := p.Write(metric); err != nil {
		t.Fatalf("expected no error, got %v", err)
	}

	if !strings.Contains(capturedBody, "container_metrics,container=sample-app") {
		t.Errorf("expected measurement+tag in body, got: %s", capturedBody)
	}
	if !strings.Contains(capturedBody, "cpu_percent=42.50") || !strings.Contains(capturedBody, "mem_percent=60.10") {
		t.Errorf("expected both fields in body, got: %s", capturedBody)
	}
	if capturedAuth != "Token test-token-123" {
		t.Errorf("expected Authorization header 'Token test-token-123', got %q", capturedAuth)
	}
	if !strings.Contains(capturedQuery, "org=hkbk") || !strings.Contains(capturedQuery, "bucket=autoscaler") {
		t.Errorf("expected org/bucket in query string, got %q", capturedQuery)
	}
}

func TestWrite_ReturnsErrorOnServerFailure(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	p := New(server.URL, "hkbk", "autoscaler", "token")
	err := p.Write(model.Metric{Container: "x", Timestamp: time.Now()})
	if err == nil {
		t.Fatalf("expected an error when server returns 500, got nil")
	}
}

func TestSanitizeTag_ReplacesLineProtocolSeparators(t *testing.T) {
	got := sanitizeTag("my app, v1=2")
	want := "my_app__v1_2"
	if got != want {
		t.Errorf("sanitizeTag() = %q, want %q", got, want)
	}
}

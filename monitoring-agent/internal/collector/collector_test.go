package collector

import "testing"

func TestParseDockerStatsLine_ValidInput(t *testing.T) {
	raw := []byte(`{"Container":"abc123","Name":"sample-app","CPUPerc":"12.34%","MemPerc":"45.67%"}`)

	metric, err := parseDockerStatsLine(raw, "sample-app")
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if metric.Container != "sample-app" {
		t.Errorf("expected container name 'sample-app', got %q", metric.Container)
	}
	if metric.CPUPercent != 12.34 {
		t.Errorf("expected CPU 12.34, got %v", metric.CPUPercent)
	}
	if metric.MemPercent != 45.67 {
		t.Errorf("expected Mem 45.67, got %v", metric.MemPercent)
	}
	if metric.Timestamp.IsZero() {
		t.Errorf("expected a non-zero timestamp")
	}
}

func TestParseDockerStatsLine_EmptyInput(t *testing.T) {
	_, err := parseDockerStatsLine([]byte(""), "sample-app")
	if err == nil {
		t.Fatalf("expected an error for empty input, got nil")
	}
}

func TestParseDockerStatsLine_MalformedJSON(t *testing.T) {
	_, err := parseDockerStatsLine([]byte("not json"), "sample-app")
	if err == nil {
		t.Fatalf("expected an error for malformed JSON, got nil")
	}
}

func TestParseDockerStatsLine_FallsBackToProvidedNameWhenMissing(t *testing.T) {
	raw := []byte(`{"Container":"abc123","Name":"","CPUPerc":"1.0%","MemPerc":"2.0%"}`)

	metric, err := parseDockerStatsLine(raw, "fallback-name")
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if metric.Container != "fallback-name" {
		t.Errorf("expected fallback name 'fallback-name', got %q", metric.Container)
	}
}

func TestParsePercent(t *testing.T) {
	cases := map[string]float64{
		"12.34%": 12.34,
		"0.00%":  0.0,
		"100%":   100.0,
		" 5.5% ": 5.5,
	}
	for input, want := range cases {
		got, err := parsePercent(input)
		if err != nil {
			t.Fatalf("parsePercent(%q) returned error: %v", input, err)
		}
		if got != want {
			t.Errorf("parsePercent(%q) = %v, want %v", input, got, want)
		}
	}
}

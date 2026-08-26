package publisher

import (
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/hkbk/monitoring-agent/internal/model"
)

// Publisher writes metrics to InfluxDB 2.x using its HTTP /api/v2/write
// endpoint directly (line protocol), instead of pulling in the official
// influxdb-client-go module. That keeps this whole agent dependency-free -
// only the Go standard library is required to build it.
type Publisher struct {
	baseURL string
	org     string
	bucket  string
	token   string
	client  *http.Client
}

func New(baseURL, org, bucket, token string) *Publisher {
	return &Publisher{
		baseURL: strings.TrimRight(baseURL, "/"),
		org:     org,
		bucket:  bucket,
		token:   token,
		client:  &http.Client{Timeout: 5 * time.Second},
	}
}

// Write sends one metric as an InfluxDB line-protocol point:
//   container_metrics,container=<name> cpu_percent=<v>,mem_percent=<v> <unix-nano-timestamp>
func (p *Publisher) Write(m model.Metric) error {
	line := fmt.Sprintf(
		"container_metrics,container=%s cpu_percent=%.2f,mem_percent=%.2f %d",
		sanitizeTag(m.Container), m.CPUPercent, m.MemPercent, m.Timestamp.UnixNano(),
	)

	url := fmt.Sprintf("%s/api/v2/write?org=%s&bucket=%s&precision=ns", p.baseURL, p.org, p.bucket)

	req, err := http.NewRequest(http.MethodPost, url, strings.NewReader(line))
	if err != nil {
		return fmt.Errorf("could not build influxdb request: %w", err)
	}
	req.Header.Set("Authorization", "Token "+p.token)
	req.Header.Set("Content-Type", "text/plain; charset=utf-8")

	resp, err := p.client.Do(req)
	if err != nil {
		return fmt.Errorf("influxdb write failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 300 {
		return fmt.Errorf("influxdb write returned status %d", resp.StatusCode)
	}
	return nil
}

// sanitizeTag strips characters that would break line-protocol tag syntax
// (commas, spaces, equals signs are all field/tag separators in line protocol).
func sanitizeTag(s string) string {
	replacer := strings.NewReplacer(",", "_", " ", "_", "=", "_")
	return replacer.Replace(s)
}

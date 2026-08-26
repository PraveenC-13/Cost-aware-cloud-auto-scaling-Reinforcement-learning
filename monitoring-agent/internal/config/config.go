package config

import (
	"os"
	"strconv"
	"strings"
)

// Config holds everything the agent needs, all sourced from environment
// variables so the same binary runs unchanged locally and inside Docker.
type Config struct {
	Containers      []string // which containers to poll, e.g. "sample-app-1,sample-app-2"
	PollInterval    int      // seconds between polls
	InfluxURL       string
	InfluxOrg       string
	InfluxBucket    string
	InfluxToken     string
	HTTPPort        string
}

// Load reads config from the environment, applying sensible defaults so the
// agent still starts (and is demoable) even with zero configuration.
func Load() Config {
	return Config{
		Containers:   splitAndTrim(getEnv("CONTAINERS", "sample-app")),
		PollInterval: getEnvInt("POLL_INTERVAL_SECONDS", 10),
		InfluxURL:    getEnv("INFLUXDB_URL", "http://localhost:8086"),
		InfluxOrg:    getEnv("INFLUXDB_ORG", "hkbk"),
		InfluxBucket: getEnv("INFLUXDB_BUCKET", "autoscaler"),
		InfluxToken:  getEnv("INFLUXDB_TOKEN", ""),
		HTTPPort:     getEnv("PORT", "9100"),
	}
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func getEnvInt(key string, fallback int) int {
	if v := os.Getenv(key); v != "" {
		if parsed, err := strconv.Atoi(v); err == nil {
			return parsed
		}
	}
	return fallback
}

func splitAndTrim(csv string) []string {
	parts := strings.Split(csv, ",")
	result := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			result = append(result, p)
		}
	}
	return result
}

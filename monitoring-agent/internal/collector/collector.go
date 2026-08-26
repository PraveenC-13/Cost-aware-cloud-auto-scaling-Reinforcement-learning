package collector

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os/exec"
	"strconv"
	"strings"
	"time"

	"github.com/hkbk/monitoring-agent/internal/model"
)

// dockerStatsJSON mirrors the fields `docker stats --format '{{json .}}'`
// prints, one JSON object per line. Docker reports percentages as strings
// like "12.34%", which is why CPUPerc/MemPerc below are strings, not floats.
type dockerStatsJSON struct {
	Container string `json:"Container"`
	Name      string `json:"Name"`
	CPUPerc   string `json:"CPUPerc"`
	MemPerc   string `json:"MemPerc"`
}

// Collect shells out to the Docker CLI for a single container's live stats.
// Using the CLI instead of the Docker Go SDK keeps this agent dependency-free
// (standard library only) and avoids version-matching headaches between the
// SDK and whatever Docker Engine version each teammate's laptop runs.
func Collect(containerName string) (model.Metric, error) {
	cmd := exec.Command("docker", "stats", "--no-stream", "--format", "{{json .}}", containerName)

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		return model.Metric{}, fmt.Errorf("docker stats failed for %s: %w (%s)", containerName, err, stderr.String())
	}

	return parseDockerStatsLine(stdout.Bytes(), containerName)
}

// parseDockerStatsLine is split out from Collect() specifically so it can be
// unit tested without Docker (or any container) actually running.
func parseDockerStatsLine(raw []byte, fallbackName string) (model.Metric, error) {
	line := strings.TrimSpace(string(raw))
	if line == "" {
		return model.Metric{}, fmt.Errorf("empty docker stats output for %s", fallbackName)
	}

	var parsed dockerStatsJSON
	if err := json.Unmarshal([]byte(line), &parsed); err != nil {
		return model.Metric{}, fmt.Errorf("could not parse docker stats JSON: %w", err)
	}

	cpu, err := parsePercent(parsed.CPUPerc)
	if err != nil {
		return model.Metric{}, fmt.Errorf("could not parse CPU%%: %w", err)
	}
	mem, err := parsePercent(parsed.MemPerc)
	if err != nil {
		return model.Metric{}, fmt.Errorf("could not parse Mem%%: %w", err)
	}

	name := parsed.Name
	if name == "" {
		name = fallbackName
	}

	return model.Metric{
		Container:  name,
		CPUPercent: cpu,
		MemPercent: mem,
		Timestamp:  time.Now().UTC(),
	}, nil
}

func parsePercent(s string) (float64, error) {
	trimmed := strings.TrimSuffix(strings.TrimSpace(s), "%")
	return strconv.ParseFloat(trimmed, 64)
}

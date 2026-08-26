package model

import "time"

// Metric is one reading collected from a single container/host at a point in time.
type Metric struct {
	Container string    `json:"container"`
	CPUPercent float64  `json:"cpu_percent"`
	MemPercent float64  `json:"mem_percent"`
	Timestamp  time.Time `json:"timestamp"`
}

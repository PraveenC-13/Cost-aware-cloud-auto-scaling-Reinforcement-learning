// monitoring-agent polls Docker container stats (CPU%, memory%) for one or
// more containers at a fixed interval, pushes each reading to InfluxDB, and
// keeps the most recent reading per container in memory for quick debugging
// via GET /metrics/latest - so you can check the agent is alive without
// needing to query InfluxDB directly.
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/hkbk/monitoring-agent/internal/collector"
	"github.com/hkbk/monitoring-agent/internal/config"
	"github.com/hkbk/monitoring-agent/internal/model"
	"github.com/hkbk/monitoring-agent/internal/publisher"
)

// latestMetrics is a small in-memory cache, guarded by a mutex since it's
// written by N polling goroutines and read by the HTTP handler concurrently.
type latestMetrics struct {
	mu   sync.RWMutex
	data map[string]model.Metric
}

func newLatestMetrics() *latestMetrics {
	return &latestMetrics{data: make(map[string]model.Metric)}
}

func (l *latestMetrics) set(m model.Metric) {
	l.mu.Lock()
	defer l.mu.Unlock()
	l.data[m.Container] = m
}

func (l *latestMetrics) snapshot() map[string]model.Metric {
	l.mu.RLock()
	defer l.mu.RUnlock()
	out := make(map[string]model.Metric, len(l.data))
	for k, v := range l.data {
		out[k] = v
	}
	return out
}

func main() {
	cfg := config.Load()
	pub := publisher.New(cfg.InfluxURL, cfg.InfluxOrg, cfg.InfluxBucket, cfg.InfluxToken)
	cache := newLatestMetrics()

	log.Printf("monitoring-agent starting: containers=%v interval=%ds influx=%s",
		cfg.Containers, cfg.PollInterval, cfg.InfluxURL)

	// One goroutine per container - this is the concurrency Go is good at.
	// Polling N containers never blocks on any single one being slow.
	var wg sync.WaitGroup
	for _, container := range cfg.Containers {
		wg.Add(1)
		go func(name string) {
			defer wg.Done()
			pollLoop(name, time.Duration(cfg.PollInterval)*time.Second, pub, cache)
		}(container)
	}

	startHTTPServer(cfg.HTTPPort, cache)

	// startHTTPServer blocks forever (ListenAndServe), so this line only
	// matters if that ever returns due to a fatal server error.
	wg.Wait()
}

func pollLoop(container string, interval time.Duration, pub *publisher.Publisher, cache *latestMetrics) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		metric, err := collector.Collect(container)
		if err != nil {
			log.Printf("[%s] collect error: %v", container, err)
		} else {
			cache.set(metric)
			if err := pub.Write(metric); err != nil {
				log.Printf("[%s] publish error: %v", container, err)
			}
		}
		<-ticker.C
	}
}

func startHTTPServer(port string, cache *latestMetrics) {
	mux := http.NewServeMux()

	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"status":"ok"}`))
	})

	mux.HandleFunc("/metrics/latest", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(cache.snapshot()); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
		}
	})

	addr := ":" + port
	log.Printf("monitoring-agent HTTP server listening on %s", addr)

	go func() {
		if err := http.ListenAndServe(addr, mux); err != nil {
			log.Fatalf("HTTP server failed: %v", err)
		}
	}()
}

// Copyright 2026 The OpenEBS Authors.
// Licensed under the Apache License, Version 2.0.

// Package config owns the legacy annotation wire format without depending on Maya.
package config

import (
	"fmt"
	"strings"

	"sigs.k8s.io/yaml"
)

const (
	CASConfigKey = "cas.openebs.io/config"
	CASTypeKey   = "openebs.io/cas-type"
	ValuePTP     = "value"
)

// Config retains the serialized configuration accepted by released provisioners.
type Config struct {
	Name    string            `json:"name"`
	Enabled string            `json:"enabled"`
	Value   string            `json:"value"`
	Data    map[string]string `json:"data"`
	List    []string          `json:"list"`
}

func UnMarshallToConfig(value string) ([]Config, error) {
	var configs []Config
	err := yaml.Unmarshal([]byte(value), &configs)
	return configs, err
}

// MergeConfig preserves higher-priority entries as whole records, including Data.
func MergeConfig(high, low []Config) []Config {
	merged := append([]Config(nil), high...)
	seen := make(map[string]bool, len(high))
	for _, item := range high {
		seen[strings.TrimSpace(item.Name)] = true
	}
	for _, item := range low {
		if !seen[strings.TrimSpace(item.Name)] {
			merged = append(merged, item)
		}
	}
	return merged
}

func ConfigToMap(configs []Config) (map[string]interface{}, error) {
	result := make(map[string]interface{}, len(configs))
	for _, item := range configs {
		name := strings.TrimSpace(item.Name)
		if name == "" {
			return nil, fmt.Errorf("failed to transform cas config to map: missing config name")
		}
		// Duplicate names historically use the last entry.
		result[name] = map[string]string{"enabled": item.Enabled, ValuePTP: item.Value}
	}
	return result, nil
}

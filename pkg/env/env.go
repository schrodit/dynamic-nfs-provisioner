// Copyright 2026 The OpenEBS Authors.
// Licensed under the Apache License, Version 2.0.

package env

import (
	"os"
	"strconv"
	"strings"
)

// ENVKey preserves the environment getter contract used by the provisioner.
type ENVKey string

const (
	OpenEBSNamespace       ENVKey = "OPENEBS_NAMESPACE"
	OpenEBSServiceAccount  ENVKey = "OPENEBS_SERVICE_ACCOUNT"
	OpenEBSEnableAnalytics ENVKey = "OPENEBS_IO_ENABLE_ANALYTICS"
)

func Get(key ENVKey) string { return strings.TrimSpace(os.Getenv(string(key))) }

func GetOrDefault(key ENVKey, fallback string) string {
	if value := Get(key); value != "" {
		return value
	}
	return fallback
}

func Truthy(key ENVKey) bool {
	value, _ := strconv.ParseBool(Get(key))
	return value
}

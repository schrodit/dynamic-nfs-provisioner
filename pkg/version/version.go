// Copyright 2026 The OpenEBS Authors.
// Licensed under the Apache License, Version 2.0.

package version

var (
	Version   = "development"
	GitCommit = "unknown"
)

func GetVersionDetails() string {
	commit := GitCommit
	if len(commit) > 7 {
		commit = commit[:7]
	}
	return Version + "-" + commit
}

// Copyright 2026 The OpenEBS Authors.
// Licensed under the Apache License, Version 2.0.

package config

import (
	"testing"
)

func TestLegacyAnnotationMerge(t *testing.T) {
	pvc, err := UnMarshallToConfig(`
- name: BackendStorageClass
  value: pvc-storage
- name: FilePermissions
  data:
    UID: "1234"
    GID: "2345"
    mode: "640"
`)
	if err != nil {
		t.Fatal(err)
	}
	sc, err := UnMarshallToConfig(`[{"name":" BackendStorageClass ","value":"sc-storage"}]`)
	if err != nil {
		t.Fatal(err)
	}
	merged := MergeConfig(sc, MergeConfig(pvc, []Config{{Name: "BackendStorageClass", Value: "default"}, {Name: "NFSServerType", Value: "kernel"}}))
	values, err := ConfigToMap(merged)
	if err != nil {
		t.Fatal(err)
	}
	if values["BackendStorageClass"].(map[string]string)["value"] != "sc-storage" {
		t.Fatal("StorageClass must override PVC and defaults")
	}
	if len(merged) != 3 || merged[1].Data["UID"] != "1234" || merged[1].Data["mode"] != "640" {
		t.Fatal("FilePermissions data must survive merging")
	}
	values, err = ConfigToMap([]Config{{Name: "duplicate", Value: "first"}, {Name: "duplicate", Value: "last"}})
	if err != nil || values["duplicate"].(map[string]string)["value"] != "last" {
		t.Fatal("legacy duplicate handling changed")
	}
	if _, err := ConfigToMap([]Config{{Name: " "}}); err == nil {
		t.Fatal("empty config names must be rejected")
	}
}

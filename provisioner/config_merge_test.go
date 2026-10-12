// Copyright 2026 The OpenEBS Authors.
// Licensed under the Apache License, Version 2.0.

package provisioner

import (
	"testing"

	config "github.com/openebs/dynamic-nfs-provisioner/pkg/config"
	corev1 "k8s.io/api/core/v1"
	storagev1 "k8s.io/api/storage/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes/fake"
)

func TestVolumeConfigPrecedence(t *testing.T) {
	name := "nfs-test"
	p := &Provisioner{
		defaultConfig: []config.Config{{Name: KeyPVBackendStorageClass, Value: "default"}},
		kubeClient: fake.NewSimpleClientset(&storagev1.StorageClass{
			ObjectMeta: metav1.ObjectMeta{Name: name, Annotations: map[string]string{
				config.CASConfigKey: "- name: BackendStorageClass\n  value: sc-storage\n",
			}},
		}),
	}
	pvc := &corev1.PersistentVolumeClaim{
		ObjectMeta: metav1.ObjectMeta{Name: "claim", Namespace: "client", Annotations: map[string]string{
			config.CASConfigKey: "- name: BackendStorageClass\n  value: pvc-storage\n- name: FilePermissions\n  data:\n    UID: \"1234\"\n    GID: \"2345\"\n    mode: \"640\"\n",
		}},
		Spec: corev1.PersistentVolumeClaimSpec{StorageClassName: &name},
	}
	actual, err := p.GetVolumeConfig("pv-test", pvc)
	if err != nil {
		t.Fatal(err)
	}
	if actual.GetBackendStorageClassFromConfig() != "sc-storage" || actual.GetFsUID() != "1234" {
		t.Fatal("annotation precedence or ownership changed")
	}
	gid, err := actual.GetFsGID()
	if err != nil || gid != "2345" {
		t.Fatalf("GID changed: %q, %v", gid, err)
	}
	mode, err := actual.GetFsMode()
	if err != nil || mode != "640" {
		t.Fatalf("mode changed: %q, %v", mode, err)
	}
}

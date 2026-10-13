// Copyright 2026 The OpenEBS Authors.
// Licensed under the Apache License, Version 2.0.

package chart

import (
	"os/exec"
	"strings"
	"testing"

	appsv1 "k8s.io/api/apps/v1"
	rbacv1 "k8s.io/api/rbac/v1"
	"sigs.k8s.io/yaml"
)

func render(t *testing.T, values ...string) ([]byte, error) {
	t.Helper()
	if _, err := exec.LookPath("helm"); err != nil {
		t.Skip("helm is required for chart tests")
	}
	args := []string{"template", "test", "../../deploy/helm/charts", "--kube-version", "1.37.1"}
	for _, value := range values {
		args = append(args, "--set", value)
	}
	return exec.Command("helm", args...).CombinedOutput()
}

func TestGarbageCollectionAndSecurity(t *testing.T) {
	output, err := render(t, "nfsProvisioner.enableGarbageCollection=false")
	if err != nil {
		t.Fatalf("%v: %s", err, output)
	}
	deploymentFound, roleFound := false, false
	for _, document := range strings.Split(string(output), "\n---\n") {
		var meta struct{ Kind string }
		if err := yaml.Unmarshal([]byte(document), &meta); err != nil {
			t.Fatal(err)
		}
		switch meta.Kind {
		case "Deployment":
			deploymentFound = true
			var deployment appsv1.Deployment
			if err := yaml.Unmarshal([]byte(document), &deployment); err != nil {
				t.Fatal(err)
			}
			pod := deployment.Spec.Template.Spec
			if pod.SecurityContext == nil || pod.SecurityContext.RunAsNonRoot == nil || !*pod.SecurityContext.RunAsNonRoot {
				t.Fatal("controller must run without root")
			}
			container := pod.Containers[0]
			if container.SecurityContext == nil || container.SecurityContext.AllowPrivilegeEscalation == nil || *container.SecurityContext.AllowPrivilegeEscalation {
				t.Fatal("controller privilege escalation enabled")
			}
			gc := ""
			for _, env := range container.Env {
				if env.Name == "OPENEBS_IO_NFS_SERVER_GARBAGE_COLLECTION_ENABLED" {
					gc = env.Value
				}
			}
			if gc != "false" {
				t.Fatalf("disabling GC must reach the controller, got %q", gc)
			}
		case "ClusterRole":
			roleFound = true
			var role rbacv1.ClusterRole
			if err := yaml.Unmarshal([]byte(document), &role); err != nil {
				t.Fatal(err)
			}
			for _, rule := range role.Rules {
				for _, value := range append(append(rule.APIGroups, rule.Resources...), rule.Verbs...) {
					if value == "*" || value == "secrets" || value == "nodes/proxy" || value == "pods/exec" {
						t.Fatalf("excessive controller permission: %s", value)
					}
				}
			}
		case "PodSecurityPolicy":
			t.Fatal("removed Kubernetes resource rendered")
		}
	}
	if !deploymentFound || !roleFound {
		t.Fatal("expected controller and RBAC resources")
	}
}

func TestUnsupportedValuesFail(t *testing.T) {
	for _, test := range []struct{ value, reason string }{
		{"rbac.pspEnabled=true", "PodSecurityPolicy was removed"},
		{"nfsProvisioner.privileged=false", "kernel NFS servers require privileged"},
		{"nfsStorageClass.reclaimPolicy=invalid", "reclaimPolicy"},
	} {
		t.Run(test.value, func(t *testing.T) {
			output, err := render(t, test.value)
			if err == nil || !strings.Contains(string(output), test.reason) {
				t.Fatalf("expected useful rejection, got %v: %s", err, output)
			}
		})
	}
}

func TestDigestOverridesTag(t *testing.T) {
	digest := "sha256:" + strings.Repeat("a", 64)
	output, err := render(t, "nfsProvisioner.image.tag=ignored", "nfsProvisioner.image.digest="+digest,
		"nfsProvisioner.nfsServerAlpineImage.digest="+digest)
	if err != nil {
		t.Fatalf("%v: %s", err, output)
	}
	if !strings.Contains(string(output), "ghcr.io/schrodit/provisioner-nfs@"+digest) ||
		!strings.Contains(string(output), "ghcr.io/schrodit/nfs-server-alpine@"+digest) {
		t.Fatal("immutable image references were not used")
	}
}

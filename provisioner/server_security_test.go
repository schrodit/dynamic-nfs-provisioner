// Copyright 2026 The OpenEBS Authors.
// Licensed under the Apache License, Version 2.0.

package provisioner

import (
	"context"
	"testing"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes/fake"
)

func TestNFSDeploymentSecurity(t *testing.T) {
	t.Setenv(string(NFSServerImageKey), "example.invalid/nfs:fixture")
	p := &Provisioner{serverNamespace: "servers", kubeClient: fake.NewSimpleClientset()}
	opts := &KernelNFSServerOptions{pvName: "test", backendPvcName: "backend", ctx: context.Background()}
	if err := p.createDeployment(opts); err != nil {
		t.Fatal(err)
	}
	deployment, err := p.kubeClient.AppsV1().Deployments("servers").Get(context.Background(), "nfs-test", metav1.GetOptions{})
	if err != nil {
		t.Fatal(err)
	}
	pod := deployment.Spec.Template.Spec
	if pod.AutomountServiceAccountToken == nil || *pod.AutomountServiceAccountToken {
		t.Fatal("NFS servers must not receive API credentials")
	}
	if pod.Containers[0].SecurityContext.Privileged == nil || !*pod.Containers[0].SecurityContext.Privileged {
		t.Fatal("kernel NFS server requires privileges")
	}
}

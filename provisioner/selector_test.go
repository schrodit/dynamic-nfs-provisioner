// Copyright 2026 The OpenEBS Authors.
// Licensed under the Apache License, Version 2.0.

package provisioner

import (
	"testing"

	v1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/labels"
)

func TestNodeSelectorMatching(t *testing.T) {
	tests := []struct {
		operator        v1.NodeSelectorOperator
		values          []string
		matching, other labels.Set
	}{
		{v1.NodeSelectorOpIn, []string{"west"}, labels.Set{"zone": "west"}, labels.Set{"zone": "east"}},
		{v1.NodeSelectorOpNotIn, []string{"west"}, labels.Set{}, labels.Set{"zone": "west"}},
		{v1.NodeSelectorOpExists, nil, labels.Set{"zone": ""}, labels.Set{}},
		{v1.NodeSelectorOpDoesNotExist, nil, labels.Set{}, labels.Set{"zone": ""}},
		{v1.NodeSelectorOpGt, []string{"3"}, labels.Set{"zone": "4"}, labels.Set{"zone": "3"}},
		{v1.NodeSelectorOpLt, []string{"3"}, labels.Set{"zone": "2"}, labels.Set{"zone": "invalid"}},
	}
	for _, test := range tests {
		t.Run(string(test.operator), func(t *testing.T) {
			selector, err := nodeSelectorRequirementsAsSelector([]v1.NodeSelectorRequirement{{Key: "zone", Operator: test.operator, Values: test.values}})
			if err != nil {
				t.Fatal(err)
			}
			if !selector.Matches(test.matching) || selector.Matches(test.other) {
				t.Fatal("selector semantics changed")
			}
		})
	}
	for _, requirement := range []v1.NodeSelectorRequirement{
		{Key: "zone", Operator: v1.NodeSelectorOpIn},
		{Key: "zone", Operator: v1.NodeSelectorOpExists, Values: []string{"invalid"}},
		{Key: "zone", Operator: v1.NodeSelectorOpGt, Values: []string{"invalid"}},
		{Key: "zone", Operator: "unsupported"},
	} {
		if _, err := nodeSelectorRequirementsAsSelector([]v1.NodeSelectorRequirement{requirement}); err == nil {
			t.Fatal("invalid selector accepted")
		}
	}
}

/*
Copyright 2021 The OpenEBS Authors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package provisioner

import (
	"fmt"
	"sync"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestProvisioningTrackerConcurrent(t *testing.T) {
	tracker := NewProvisioningTracker()
	var workers sync.WaitGroup
	for worker := 0; worker < 20; worker++ {
		workers.Add(1)
		go func(id int) {
			defer workers.Done()
			name := fmt.Sprintf("pv-%d", id)
			for request := 0; request < 100; request++ {
				tracker.Add(name)
				if !tracker.Inprogress(name) {
					t.Errorf("active request %s missing", name)
				}
				tracker.Inprogress("pv-0") // Garbage collection reads while other requests change.
				tracker.Delete(name)
				if tracker.Inprogress(name) {
					t.Errorf("completed request %s remains", name)
				}
			}
		}(worker)
	}
	workers.Wait()
}

func TestProvisioningTracker(t *testing.T) {
	tracker := NewProvisioningTracker()

	assert.False(t, tracker.Inprogress("pv1"))

	tracker.Add("pv1")
	tracker.Add("pv2")

	assert.True(t, tracker.Inprogress("pv1"))
	assert.True(t, tracker.Inprogress("pv2"))

	tracker.Delete("pv1")
	assert.False(t, tracker.Inprogress("pv1"))
	assert.True(t, tracker.Inprogress("pv2"))

	tracker.Delete("pv2")
	assert.False(t, tracker.Inprogress("pv2"))
}

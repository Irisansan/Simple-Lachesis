package lachesis

import (
	"Lachesis/inputs"
	"fmt"
)

func ForklessCause(eventaId string, eventbId string, events inputs.Events, validators Validators) bool {
	a := HighestEventsObservedBy(eventaId, events)    // map[branch]seq+IsFork
	b := LowestEventsWhichDoObserve(eventbId, events) // map[branch]seq
	eventB := events[eventbId]
	branchB := eventB.Creator()
	vector := a[branchB]
	if vector.IsFork() {
		fmt.Println("There is a fork in branch:", branchB)
		return false // A observe a fork from B's branch
	}
	yes := uint32(0)
	total := TotalWeight(validators)
	for branch, _ := range validators {
		// validator observed B (and no fork) in the subgraph of A
		vector := a[branch]
		if b[branch] <= vector.Seq() && b[branch] != 0 && !vector.IsFork() {
			yes += validators[branch].weight
		} else if vector.IsFork() {
			fmt.Println("There is a fork in branch:", branch)
			total -= validators[branch].weight
		}
	}
	quorum := total / 3 * 2
	return yes > quorum
}

func HighestEventsObservedBy(eID string, events inputs.Events) map[string]inputs.Vector {
	vector := make(map[string]inputs.Vector)
	event := events[eID]
	vector = event.HighestEventsVector()
	return vector
}

func LowestEventsWhichDoObserve(eID string, events inputs.Events) map[string]uint32 {
	b := make(map[string]uint32)
	for _, v := range events {
		var p = v.Parents()
		for _, j := range p {
			if j == eID {
				_, flag := b[v.Creator()]
				if flag {
					if b[v.Creator()] > v.Seq() {
						b[v.Creator()] = v.Seq()
					}
				} else {
					b[v.Creator()] = v.Seq()
				}
			}
		}
	}
	return b
}

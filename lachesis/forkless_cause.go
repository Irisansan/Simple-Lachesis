package lachesis

import (
	"Lachesis/inputs"
)

// predefine we have 4 validators
var branches uint32 = 4

func ForklessCause(eventaId string, eventbId string, events inputs.Events, validators Validators) bool {
	a := HighestEventsObservedBy(eventaId, events)    // map[branch]seq+IsFork
	b := LowestEventsWhichDoObserve(eventbId, events) // map[branch]seq
	eventB := events[eventbId]
	branchB := eventB.Creator()
	if IsFork(eventaId, eventbId, branchB, events) {
		return false // A observe a fork from B's branch
	}
	yes := uint32(0)
	for branch := uint32(0); branch < branches; branch++ {
		// validator observed B (and no fork) in the subgraph of A
		if b[branch] <= a[branch] && b[branch] != 0 && !IsFork(eventaId, eventbId, branch, events) {
			yes += validators[branch].weight
		}
	}
	return yes > TotalWeight(validators)/3*2

}

func IsFork(eventaId string, eventbId string, branch uint32, events inputs.Events) bool {
	a := HighestEventsObservedBy(eventaId, events)
	b := LowestEventsWhichDoObserve(eventbId, events)
	detected := make(map[uint32]uint32)
	for _, e := range events {
		if e.Creator() == branch && e.Seq() < a[branch] && e.Seq() > b[branch] {
			epoch, flag := detected[e.Seq()]
			if flag && epoch == e.Epoch() {
				return true // Fork exists
			}
			detected[e.Seq()] = e.Epoch()
		}
	}
	return false
}

func HighestEventsObservedBy(eID string, events inputs.Events) map[uint32]uint32 {
	e, _ := events[eID]
	var p = e.Parents()
	a := make(map[uint32]uint32)
	for k, v := range events {
		for i := 0; i < len(p); i++ {
			if k == p[i] {
				_, flag := a[v.Creator()]
				if flag {
					if a[v.Creator()] < v.Seq() {
						a[v.Creator()] = v.Seq()
					}
				} else {
					a[v.Creator()] = v.Seq()
				}
			}
		}
	}
	return a
}

func LowestEventsWhichDoObserve(eID string, events inputs.Events) map[uint32]uint32 {
	b := make(map[uint32]uint32)
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

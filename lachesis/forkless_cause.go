package lachesis

import (
	"Lachesis/inputs"
	"Lachesis/pos"
	"fmt"
)

func ForklessCause(eventaId inputs.EventId, eventbId inputs.EventId, events inputs.Events, validators pos.Validators) bool {
	a := HighestEventsObservedBy(eventaId, events)    // map[branch]seq+IsFork
	b := LowestEventsWhichDoObserve(eventbId, events) // map[branch]seq
	eventB := events[eventbId]
	branchB := eventB.Creator()
	vector := a[branchB]
	if vector.IsFork() {
		fmt.Println("There is a fork in branch:", branchB)
		return false // A observe a fork from B's branch
	}
	yes := validators.NewCounter()
	total := validators.TotalWeight()
	for _, branch := range validators.Branch() {
		// validator observed B (and no fork) in the subgraph of A
		vector := a[branch]
		if b[branch] <= vector.Seq() && b[branch] != 0 && !vector.IsFork() {
			yes.Count(branch)
		} else if vector.IsFork() {
			fmt.Println("There is a fork in branch:", branch)
			validator := validators.Validator()
			total -= validator[branch]
		}
	}
	quorum := total/3*2 + 1
	return yes.SumWeight() > quorum
}

func HighestEventsObservedBy(eID inputs.EventId, events inputs.Events) map[inputs.ValidatorId]inputs.Vector {
	vector := make(map[inputs.ValidatorId]inputs.Vector)
	event := events[eID]
	vector = event.HighestEventsVector()
	return vector
}

func LowestEventsWhichDoObserve(eID inputs.EventId, events inputs.Events) map[inputs.ValidatorId]inputs.Seq {
	b := make(map[inputs.ValidatorId]inputs.Seq)
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

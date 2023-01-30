package lachesis

import (
	"Lachesis/dag"
	"Lachesis/idx"
	"fmt"
)

func ForklessCause(eventA dag.Event, eventB dag.Event, store Store) bool {
	a := HighestEventsObservedBy(eventA)                  // map[branch]seq+IsFork
	b := LowestEventsWhichDoObserve(eventB, store.events) // map[branch]seq
	branchB := eventB.Creator()
	vector := a[branchB]
	if vector.IsFork() {
		fmt.Println("There is a fork in branch:", branchB)
		return false // A observe a fork from B's branch
	}
	yes := store.validators.NewCounter()
	total := store.validators.TotalWeight()
	for _, branch := range store.validators.Branch() {
		// validator observed B (and no fork) in the subgraph of A
		vector := a[branch]
		if b[branch] <= vector.Seq() && b[branch] != 0 && !vector.IsFork() {
			yes.Count(branch)
		} else if vector.IsFork() {
			fmt.Println("There is a fork in branch:", branch)
			validator := store.validators.Validator()
			total -= validator[branch]
		}
	}
	quorum := total/3*2 + 1
	return yes.SumWeight() > quorum
}

func HighestEventsObservedBy(event dag.Event) map[idx.ValidatorId]dag.Vector {
	vector := make(map[idx.ValidatorId]dag.Vector)
	vector = event.HighestEventsVector()
	return vector
}

// This is wrong!
func LowestEventsWhichDoObserve(e dag.Event, events dag.Events) map[idx.ValidatorId]idx.Seq {
	b := make(map[idx.ValidatorId]idx.Seq)
	for _, v := range events {
		var p = v.Parents()
		for _, j := range p {
			if j == e.Id() {
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

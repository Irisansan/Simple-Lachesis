package lachesis

import (
	"Lachesis/dag"
	"Lachesis/idx"
	"fmt"
)

func ForklessCause(eventA dag.Event, eventB dag.Event, store Store) bool {
	a := HighestEventsObservedBy(eventA)    // map[branch]seq+IsFork
	b := LowestEventsWhichDoObserve(eventB) // map[branch]seq
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
		beforeVector := a[branch]
		afterVector := b[branch]
		if afterVector.Seq() <= beforeVector.Seq() && afterVector.Seq() != 0 && !beforeVector.IsFork() {
			yes.Count(branch)
		} else if beforeVector.IsFork() {
			fmt.Println("There is a fork in branch:", branch)
			validator := store.validators.Validators()
			total -= validator[branch]
		}
	}
	quorum := total/3*2 + 1
	return yes.SumWeight() >= quorum
}

func HighestEventsObservedBy(event dag.Event) map[idx.ValidatorId]dag.BeforeVector {
	vector := make(map[idx.ValidatorId]dag.BeforeVector)
	vector = event.HighestEventsVector()
	return vector
}

// This is wrong!
func LowestEventsWhichDoObserve(event dag.Event) map[idx.ValidatorId]dag.AfterVector {
	vector := make(map[idx.ValidatorId]dag.AfterVector)
	vector = event.LowestEventsVector()
	return vector
}

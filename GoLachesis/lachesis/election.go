package lachesis

import (
	"Lachesis/dag"
	"Lachesis/idx"
)

// Election is cached data of election algorithm.
type Election struct {
	// election state
	decidedRoots    map[idx.ValidatorId]voteValue // decided roots at "frameToDecide"
	votes           map[voteID]voteValue
	sortDecidedRoot []dag.Event

	store Store
}

// NewElection initializes the election
func (el *Election) NewElection() {
	el.votes = make(map[voteID]voteValue)
	el.decidedRoots = make(map[idx.ValidatorId]voteValue)
	el.sortDecidedRoot = nil
}

// UpdateStore updates the store when a new root comes
func (el *Election) UpdateStore(store Store) { el.store = store }

// Votes
type (
	voteID struct {
		fromRoot     idx.EventId
		forValidator idx.ValidatorId
	}
	voteValue struct {
		decided      bool
		yes          bool
		observedRoot dag.Event
	}
)

// Res defines the final election result, i.e. decided frame
type Res struct {
	Frame   idx.Frame
	Atropos dag.Event
}

// Atropos stores the elected atropos and the decided frames
type Atropos struct {
	DecidedFrames []idx.Frame
	AtroposList   []dag.Event
}

func (a *Atropos) StoreDecidedFrames(frame idx.Frame) {
	a.DecidedFrames = append(a.DecidedFrames, frame)
}
func (a *Atropos) StoreAtropos(atropos dag.Event) {
	a.AtroposList = append(a.AtroposList, atropos)
}

func (a *Atropos) LastDecidedFrame() idx.Frame {
	return a.DecidedFrames[len(a.DecidedFrames)-1]
}

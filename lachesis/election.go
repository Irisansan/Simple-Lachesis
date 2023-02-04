package lachesis

import (
	"Lachesis/dag"
	"Lachesis/idx"
)

// Election is cached data of election algorithm.
type Election struct {
	// election params
	lastDecidedFrame idx.Frame

	store Store

	// election state
	decidedRoots map[idx.ValidatorId]voteValue // decided roots at "frameToDecide"
	votes        map[voteID]voteValue
}

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

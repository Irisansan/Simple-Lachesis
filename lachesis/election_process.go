package lachesis

import (
	"Lachesis/dag"
	"Lachesis/idx"
	"Lachesis/pos"
)

// ProcessRoot calculates Atropos votes only for the new root.
// If this root observes that the current election is decided, then return decided Atropos
func (el *Election) ProcessRoot(newRoot dag.Event) *Res {
	frameToDecide := el.lastDecidedFrame + 1
	round := newRoot.Frame() - frameToDecide

	// the frame does not decide about itself
	if round == 0 {
		return nil
	}

	// previous frame roots, which newRoot forkless cause
	prevRoots := el.ObservedRootsInGivenFrame(newRoot, newRoot.Frame()-1)

	// All validatorId
	vv := el.store.Validators()
	validators := vv.Validators()
	// To get (validators - decidedRoots.keys)
	val := make(map[idx.ValidatorId]pos.Weight)
	for v, w := range validators {
		if _, exist := el.decidedRoots[v]; exist == false {
			val[v] = w
		}
	}

	for validator := range val {
		voteid := voteID{}
		votevalue := voteValue{}
		if round == 1 {
			// vote yes for the candidate if newRoot forkless causes it
			voteid.fromRoot = newRoot.Id()
			voteid.forValidator = validator
			// To check prevRoots[validator].exists
			for _, r := range prevRoots {
				if r.Creator() == validator {
					votevalue.yes = true
					votevalue.observedRoot = r
				}
			}
			votevalue.decided = false

			el.votes[voteid] = votevalue

		} else {
			candidate := dag.Event{}
			var yesVotes pos.Weight = 0
			var noVotes pos.Weight = 0
			for _, prevRoot := range prevRoots {
				voteid.fromRoot = prevRoot.Id()
				voteid.forValidator = validator
				prevVote := el.votes[voteid]
				if prevVote.yes {
					candidate = prevVote.observedRoot
					yesVotes += el.store.validators.GetWeightById(prevRoot.Creator())
				} else {
					noVotes += el.store.validators.GetWeightById(prevRoot.Creator())
				}
			}
			votevalue.yes = yesVotes >= noVotes
			votevalue.observedRoot = candidate
			votevalue.decided = el.store.validators.HasQuorum(yesVotes) || el.store.validators.HasQuorum(noVotes)
			if votevalue.decided {
				el.decidedRoots[validator] = votevalue
			}
		}
	}
	// Not finished yet
	return nil // nil if no decided root
}

func (el *Election) ObservedRootsInGivenFrame(root dag.Event, frame idx.Frame) Roots {
	roots := el.store.Roots(frame)
	var observedRoots Roots
	for _, r := range roots {
		if ForklessCause(root, r, el.store) {
			observedRoots = append(observedRoots, r)
		}
	}
	return observedRoots
}

func (el *Election) chooseAtropos() {

}

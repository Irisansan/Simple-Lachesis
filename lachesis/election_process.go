package lachesis

import (
	"Lachesis/dag"
	"Lachesis/idx"
	"Lachesis/pos"
	"fmt"
)

// ProcessRoot calculates Atropos votes only for the new root.
// If this root observes that the current election is decided, then return decided Atropos
func (el *Election) ProcessRoot(newRoot dag.Event, frameToDecide idx.Frame) *Res {
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
	for validatorId, weight := range validators {
		if _, exist := el.decidedRoots[validatorId]; exist == false {
			val[validatorId] = weight
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
				preVoteid := voteID{}
				preVoteid.fromRoot = prevRoot.Id()
				preVoteid.forValidator = validator
				prevVote := el.votes[preVoteid]
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
				if votevalue.yes {
					el.sortDecidedRoot = append(el.sortDecidedRoot, votevalue.observedRoot)
				}
			}
			voteid.fromRoot = newRoot.Id()
			voteid.forValidator = validator
			el.votes[voteid] = votevalue
		}
	}

	atropos := el.firstYesVote()

	return atropos // nil if no decided root
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

func (el *Election) firstYesVote() *Res {
	if el.sortDecidedRoot == nil {
		fmt.Println("all the roots are decided as 'no'")
		return nil
	} else {
		result := Res{}
		result.Frame = el.sortDecidedRoot[0].Frame()
		result.Atropos = el.sortDecidedRoot[0]
		fmt.Println("The Atropos is ", result.Atropos.Id(), "from frame ", result.Frame)
		return &result
	}
}

// Reset erases the current election state, prepare for new election frame
func (el *Election) Reset(store Store) {
	el.store = store
	el.votes = make(map[voteID]voteValue)
	el.decidedRoots = make(map[idx.ValidatorId]voteValue)
	el.sortDecidedRoot = nil
}

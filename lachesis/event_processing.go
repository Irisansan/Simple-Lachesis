package lachesis

import (
	"Lachesis/dag"
	"Lachesis/idx"
)

// ForklessCausedByQuorumOn returns true if event is forkless caused by 2/3W +1 roots on specified frame
func ForklessCausedByQuorumOn(event dag.Event, f Roots, store Store) bool {
	observed := store.validators.NewCounter()
	for _, root := range f {
		if ForklessCause(event, root, store) {
			observed.Count(root.Creator())
		}
	}
	if observed.HasQuorum() {
		return true
	}
	return false
}

// CalcFrameIdx checks root-conditions for new event and returns event's frame.
func (s *Store) CalcFrameIdx(e dag.Event) idx.Frame {
	selfParentFrame := idx.Frame(0)
	frame := idx.Frame(0)
	if e.SelfParent() != nil {
		event := s.events[*e.SelfParent()]
		selfParentFrame = event.Frame()
	}

	// Root
	if e.Seq() == 1 {
		frame = 0
		s.StoreFrames(frame, e)
	} else {
		frame = selfParentFrame
		if ForklessCausedByQuorumOn(e, s.Roots(frame), *s) {
			frame++
			s.StoreFrames(frame, e)
		}
	}
	return frame
}

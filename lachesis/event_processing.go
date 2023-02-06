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
func (s *Store) CalcFrameIdx(e dag.Event, el *Election) idx.Frame {
	selfParentFrame := idx.Frame(0)
	frame := idx.Frame(0)
	if e.SelfParent() != nil {
		event := s.events[*e.SelfParent()]
		selfParentFrame = event.Frame()
	}

	// Store root and its frame id
	if e.Seq() == 1 {
		frame = 0
		s.StoreFrames(frame, e)
		el.UpdateStore(*s)
		el.ProcessRoot(e, frame)
	} else {
		frame = selfParentFrame
		if ForklessCausedByQuorumOn(e, s.Roots(frame), *s) {
			frame++
			s.StoreFrames(frame, e)
			el.UpdateStore(*s)
			if s.DecidedFrames == nil {
				res := el.ProcessRoot(e, idx.Frame(0))
				if res != nil {
					s.StoreAtropos(res.Atropos)
					s.StoreDecidedFrames(res.Frame)
					el.NewElection()
					el.ProcessRoot(e, s.LastDecidedFrame())
				}
			} else {
				res := el.ProcessRoot(e, s.LastDecidedFrame())
				if res != nil {
					s.StoreAtropos(res.Atropos)
					s.StoreDecidedFrames(res.Frame)
					el.NewElection()
					el.ProcessRoot(e, s.LastDecidedFrame())
				}
			}
		}
	}
	return frame
}

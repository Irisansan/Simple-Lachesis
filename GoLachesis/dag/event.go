package dag

import (
	"Lachesis/idx"
)

// BeforeVector is for mapping from validatorId to highest observed event id
type BeforeVector struct {
	eventId idx.EventId
	seq     idx.Seq
	isFork  bool
}

// AfterVector is for mapping from validatorId to lowest event id
type AfterVector struct {
	eventId idx.EventId
	seq     idx.Seq
}

func (v *BeforeVector) EventId() idx.EventId { return v.eventId }
func (v *BeforeVector) Seq() idx.Seq         { return v.seq }
func (v *BeforeVector) IsFork() bool         { return v.isFork }
func (v *AfterVector) EventId() idx.EventId  { return v.eventId }
func (v *AfterVector) Seq() idx.Seq          { return v.seq }

func (v *BeforeVector) SetEventId(id idx.EventId) { v.eventId = id }
func (v *BeforeVector) SetSeq(seq idx.Seq)        { v.seq = seq }
func (v *BeforeVector) SetIsFork(fork bool)       { v.isFork = fork }
func (v *AfterVector) SetEventId(id idx.EventId)  { v.eventId = id }
func (v *AfterVector) SetSeq(seq idx.Seq)         { v.seq = seq }

// Events map[EventID]BaseEvent
type Events map[idx.EventId]Event

type Event struct {
	// epoch number (see epoch). Not less than 1.
	epoch idx.Epoch
	// seq number. Equal to self-parent’s seq + 1, if no self-parent, then 1.
	seq idx.Seq
	// frame number (see consensus). Not less than 1.
	frame idx.Frame
	// creator ID of validator which created event.
	creator idx.ValidatorId
	// node owner of the event
	node idx.NodeId
	// hash of the event
	id idx.EventId
	// list of parents (graph edges). May be empty. If Seq > 1, then ﬁrst element is self-parent.
	parents idx.Parents

	// cache
	// mapping from validatorId to highest observed event id
	highestEventsVector map[idx.ValidatorId]BeforeVector
	// mapping from validatorId to lowest event id
	lowestEventsVector map[idx.ValidatorId]AfterVector
}

func (e *Event) Epoch() idx.Epoch                                      { return e.epoch }
func (e *Event) Seq() idx.Seq                                          { return e.seq }
func (e *Event) Frame() idx.Frame                                      { return e.frame }
func (e *Event) Creator() idx.ValidatorId                              { return e.creator }
func (e *Event) Node() idx.NodeId                                      { return e.node }
func (e *Event) Id() idx.EventId                                       { return e.id }
func (e *Event) Parents() idx.Parents                                  { return e.parents }
func (e *Event) HighestEventsVector() map[idx.ValidatorId]BeforeVector { return e.highestEventsVector }
func (e *Event) LowestEventsVector() map[idx.ValidatorId]AfterVector   { return e.lowestEventsVector }

func (e *Event) SetEpoch(epoch idx.Epoch)           { e.epoch = epoch }
func (e *Event) SetSeq(seq idx.Seq)                 { e.seq = seq }
func (e *Event) SetFrame(frame idx.Frame)           { e.frame = frame }
func (e *Event) SetCreator(creator idx.ValidatorId) { e.creator = creator }
func (e *Event) SetNode(node idx.NodeId)            { e.node = node }
func (e *Event) SetId(id idx.EventId)               { e.id = id }
func (e *Event) SetParents(parents idx.Parents)     { e.parents = parents }

// SetEvent when adding a new event into dag
func (e *Event) SetEvent(events *Events) {
	e.SetHighestEventsVector(*events)
	e.SetLowestEventsVector(events)
}

// SelfParent returns event's self-parent, if any
func (e *Event) SelfParent() *idx.EventId {
	if e.seq <= 1 || len(e.parents) == 0 {
		return nil
	}
	return &e.parents[0]
}

// SetHighestEventsVector finds the highest events and detects whether there is a fork
func (e *Event) SetHighestEventsVector(events Events) {
	var vector BeforeVector
	e.highestEventsVector = make(map[idx.ValidatorId]BeforeVector)
	// find the highest events
	// root
	if e.seq == 1 || events == nil {
		vector.SetEventId(e.id)
		vector.SetSeq(e.seq)
		e.highestEventsVector[e.creator] = vector
		for eventId, event := range events {
			for _, parent := range e.parents {
				if eventId == parent {
					vector.SetEventId(event.id)
					vector.SetSeq(event.seq)
					e.highestEventsVector[event.creator] = vector
				}
			}
		}
	} else {
		for eventId, event := range events {
			for _, parent := range e.parents {
				// find the parent
				if eventId == parent {
					var vector BeforeVector
					vector.SetEventId(eventId)
					vector.SetSeq(event.Seq())
					e.highestEventsVector[event.creator] = vector
					// highest events observed by parents
					for i, j := range event.highestEventsVector {
						var ei BeforeVector
						ei = e.highestEventsVector[i]
						if j.Seq() > ei.Seq() {
							ei.SetEventId(j.EventId())
							ei.SetSeq(j.Seq())
							e.highestEventsVector[i] = ei
						}
					}

				}
			}
		}
	}

	// Flag: if there is already present a different event with the same seq and epoch from the same validator
	for _, event := range events {
		if e.id != event.Id() && e.creator == event.Creator() && e.seq == event.Seq() && e.epoch == event.Epoch() {
			var vector BeforeVector
			vector = e.highestEventsVector[e.creator]
			vector.SetIsFork(true)
			e.highestEventsVector[e.creator] = vector
		}
	}
	// This flag is then inherited for the given validator by parent events.
	for eventId, event := range events {
		for _, parent := range e.parents {
			// find the parent
			if eventId == parent {
				if event.highestEventsVector[event.creator].isFork {
					vector := e.highestEventsVector[event.creator]
					vector.SetIsFork(true)
					e.highestEventsVector[event.creator] = vector
				}
			}
		}
	}
}

// SetLowestEventsVector updates lowest observing events
func (e *Event) SetLowestEventsVector(events *Events) {
	var vector AfterVector
	vector.SetEventId(e.id)
	vector.SetSeq(e.seq)
	e.lowestEventsVector = make(map[idx.ValidatorId]AfterVector)
	parents := e.parents
	for {
		if parents != nil && len(parents) != 0 && parents[0] != "" {
			// e's parent
			for _, parent := range parents {
				parentVector := (*events)[parent].lowestEventsVector
				var onWalk idx.Parents
				if _, exist := parentVector[e.creator]; exist == false {
					parentVector[e.creator] = vector
					if (*events)[parent].creator != e.creator {
						// parents to traversal
						pparents := (*events)[parent].parents
						for _, p := range pparents {
							onWalk = append(onWalk, p)
						}
					}
				}
				parents = onWalk
			}
		} else {
			break
		}

	}

}

package inputs

// Events map[EventID]BaseEvent
type Events map[string]Event

type Event struct {
	// epoch number (see epoch). Not less than 1.
	epoch uint32
	// seq number. Equal to self-parent’s seq + 1, if no self-parent, then 1.
	seq uint32
	// frame number (see consensus). Not less than 1.
	frame uint32
	// creator ID of validator which created event.
	creator string
	// node owner of the event
	node string
	// hash of the event
	id string
	// list of parents (graph edges). May be empty. If Seq > 1, then ﬁrst element is self-parent.
	parents []string

	// mapping from validatorId to highest observed event id
	highestEventsVector map[string]Vector
}

func (e *Event) Epoch() uint32                          { return e.epoch }
func (e *Event) Seq() uint32                            { return e.seq }
func (e *Event) Frame() uint32                          { return e.frame }
func (e *Event) Creator() string                        { return e.creator }
func (e *Event) Node() string                           { return e.node }
func (e *Event) Id() string                             { return e.id }
func (e *Event) Parents() []string                      { return e.parents }
func (e *Event) HighestEventsVector() map[string]Vector { return e.highestEventsVector }

func (e *Event) SetEpoch(ep uint32)    { e.epoch = ep }
func (e *Event) SetSeq(s uint32)       { e.seq = s }
func (e *Event) SetFrame(f uint32)     { e.frame = f }
func (e *Event) SetCreator(c string)   { e.creator = c }
func (e *Event) SetNode(n string)      { e.node = n }
func (e *Event) SetId(i string)        { e.id = i }
func (e *Event) SetParents(p []string) { e.parents = p }

// SelfParent returns event's self-parent, if any
func (e *Event) SelfParent() *string {
	if e.seq <= 1 || len(e.parents) == 0 {
		return nil
	}
	return &e.parents[0]
}

func (e *Event) SetHighestEventsVector(events Events) {
	var vector Vector
	e.highestEventsVector = make(map[string]Vector)
	// find the highest events
	// root
	if e.seq == 1 || events == nil {
		vector.SetEventId(e.id)
		vector.SetSeq(e.seq)
		e.highestEventsVector[e.creator] = vector
		for k, v := range events {
			for _, r := range e.parents {
				if k == r {
					vector.SetEventId(v.id)
					vector.SetSeq(v.seq)
					e.highestEventsVector[v.creator] = vector
				}
			}
		}
	} else {
		for k, v := range events {
			for _, r := range e.parents {
				// find the parent
				if k == r {
					var vector Vector
					vector.SetEventId(k)
					vector.SetSeq(v.Seq())
					e.highestEventsVector[v.creator] = vector
					// highest events observed by parents
					for i, j := range v.highestEventsVector {
						var ei Vector
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
	for _, v := range events {
		if e.id != v.Id() && e.creator == v.Creator() && e.seq == v.Seq() && e.epoch == v.Epoch() {
			var v2 Vector
			v2 = e.highestEventsVector[e.creator]
			v2.SetIsFork(true)
			e.highestEventsVector[e.creator] = v2
		}
	}
	// This flag is then inherited for the given validator by parent events.
	for k, v := range events {
		for _, r := range e.parents {
			// find the parent
			if k == r {
				if v.highestEventsVector[v.creator].isFork {
					v2 := e.highestEventsVector[v.creator]
					v2.SetIsFork(true)
					e.highestEventsVector[v.creator] = v2
				}
			}
		}
	}
}

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
	creator uint32
	// node owner of the event
	node string
	// list of parents (graph edges). May be empty. If Seq > 1, then ﬁrst element is self-parent.
	parents []string
}

func (e *Event) Epoch() uint32     { return e.epoch }
func (e *Event) Seq() uint32       { return e.seq }
func (e *Event) Frame() uint32     { return e.frame }
func (e *Event) Creator() uint32   { return e.creator }
func (e *Event) Node() string      { return e.node }
func (e *Event) Parents() []string { return e.parents }

func (e *Event) SetEpoch(ep uint32)    { e.epoch = ep }
func (e *Event) SetSeq(s uint32)       { e.seq = s }
func (e *Event) SetFrame(f uint32)     { e.frame = f }
func (e *Event) SetCreator(c uint32)   { e.creator = c }
func (e *Event) SetNode(n string)      { e.node = n }
func (e *Event) SetParents(p []string) { e.parents = p }

// SelfParent returns event's self-parent, if any
func (e *Event) SelfParent() *string {
	if e.seq <= 1 || len(e.parents) == 0 {
		return nil
	}
	return &e.parents[0]
}

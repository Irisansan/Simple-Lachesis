package inputs

type Vector struct {
	eventId string
	seq     uint32
	isFork  bool
}

func (v *Vector) EventId() string { return v.eventId }
func (v *Vector) Seq() uint32     { return v.seq }
func (v *Vector) IsFork() bool    { return v.isFork }

func (v *Vector) SetEventId(s string) { v.eventId = s }
func (v *Vector) SetSeq(s uint32)     { v.seq = s }
func (v *Vector) SetIsFork(f bool)    { v.isFork = f }

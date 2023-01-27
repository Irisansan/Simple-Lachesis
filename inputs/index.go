package inputs

type (
	// Epoch numeration.
	Epoch uint32
	// Seq number.
	Seq uint32
	// Frame number (see consensus).
	Frame uint32
	// ValidatorId of validator which created event.
	ValidatorId string
	// NodeId Id of the node owner of the event
	NodeId string
	// EventId the identifier of an event
	EventId string
	// Parents list of parents (graph edges).
	Parents []EventId
)

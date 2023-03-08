# Simple-Lachesis

A simplified implementation of Lachesis in Go and in Python (the latter of which is still in the works) in order to simulate/mechanize runs of the protocol and examine its properties of Liveness, Safety, etc.

## PyLachesis:

- this is an implementation of Lachesis in Python
- another port/implementation of Lachesis

## GoLachesis:

- this is an implementation of Lachesis in Go
- run `main.go`
- reading files and setting the validators is currently done through `main.go`
- some sample DAGs and the script to generate them are available in `Simple-Lachesis/GoLachesis/inputs`

### Common package
Tool functions for data type converson are defined here.

### Dag package
The dag package defines interfaces for Events and Networks - basic building unit of the DAG. 

dag.Event

- epoch: epoch number. Not less than 1.
- seq: seq number. Equal to self-parent’s seq + 1, if no self-parent, then 1.
- frame: frame number (see consensus). Not less than 1.
- creator: creator ID of validator which created event.
- node: node owner of the event.
- id: hash of the event(identifier of the event).
- parents: list of parents (graph edges). May be empty. If Seq > 1, then ﬁrst element is self-parent.

### Idx package
Alias for the data types are defined here.

### Inputs package
The input events/nodes text files and dags are here. The text files should be defined as fowllows:

- About the input network file: Node Sequence; []Node connections; []Events owned by the node.
- About the input events file: the first line is the node; Event ID; Epoch; Sequence; Creator; []Parents.

### Lachesis package
The lachesis package cotains the consensus implementation.

**election.go**
data structures used in election are defined here.

**election_process.go**
atropos election process.

**event_process.go**
root slection and deciding frames.

**forkless_cause.go**
forkless cause algorithm.
**store.go**
it stores all events, validators, frames and Atropos.

### Main package
run main.go

Text files are input here and it reads file line by line in parent-child order.

### Pos package
Validator data structures and weight counter are defines.

### Why Both?

- Go is (far) more performant, but Python is easier to add changes to ad-hoc
- the idea is to leverage the benefits of both languages
- Python has more libraries for graphing and data science

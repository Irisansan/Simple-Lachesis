# GoLachesis:

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

- To get the highest events by individual validators observed by adding event: we need to iterate vectors of highest observed events of direct children of the newly added event and find maximum for each validatorId.

- To get the lowest events by individual validators which do observe the adding event: when adding a new event, we need to update the LowestObserving vector of all its parents and also their parents. As soon as it achieves an event, which has LowestObserving already set for validator of the new event, we don't update it and ignore its parents.

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

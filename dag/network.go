package dag

type Network map[string]Node

type Node struct {
	// the edges list between nodes
	connections []string
	// dag owned by the node
	//dag []event.Hash
	dag []string
}

func (n *Node) Connections() []string { return n.connections }
func (n *Node) Dag() []string         { return n.dag }

func (n *Node) SetConnections(c []string) { n.connections = c }
func (n *Node) SetDag(h []string)         { n.dag = h }

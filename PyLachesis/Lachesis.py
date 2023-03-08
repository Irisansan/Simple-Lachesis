import DAG as dag
import glob
import networkx as nx

# iterating over all graphs as part of testing, etc.
"""
graphs_directory = "inputs/graphs/graph_*.txt"

for filename in glob.glob(graphs_directory):
    graph = dag.convert_input_to_DAG(filename)
"""


class Lachesis:
    # state of Lachesis
    def __init__(self, validator=None):
        self.block = 0
        self.frame = 0
        self.epoch = 0
        self.root_sets = {}  # {root_set[i] => roots} for i in range(frame_numbers)
        self.cheater_list = []
        self.atropos_list = []
        self.validators = []
        self.adjacency_matrix = []
        self.time = 0
        self.global_vector = []
        self.events_at_step = []
        # combining DAGs will eventually be required
        self.local_dag = nx.DiGraph()
        # self.local_rich_dag - DAG with rich logging (block, frame, etc.) for events
        self.timestep_graph = (
            None  # - gDAG nodes at any given concurrent logical timestep
        )

    def check_for_roots(self):
        print(self.local_dag)
        print("check_for_roots")
        for node in self.timestep_graph.nodes(data=True):
            print(node)
            if self.local_dag.has_node(node):
                local_dag_node = self.local_dag.nodes[node]
                print("LDN", local_dag_node)
                predecessors = local_dag_node["predecessors"]
                if predecessors == 0:
                    if self.frame in self.root_sets:
                        self.root_sets[self.frame].append(node)

                validators_observed = local_dag_node["validators_observed"]
                for source, target in self.local_dag.out_edges(local_dag_node[0]):
                    source_data = self.local_dag.nodes[source]
                    target_data = self.local_dag.nodes[target]
                    target_validator = target[0]
                    print(validators_observed, target_validator)
                    if target_validator not in validators_observed:
                        source_validator = source[0]
                        if source_validator != target_validator:
                            target_weight = target_data["weight"]
                            if (
                                target_validator
                                in source_data["validators_observed"]
                            ):
                                source_data["validators_observed"][
                                    target_validator
                                ] += target_weight
                            else:
                                source_data["validators_observed"][
                                    target_validator
                                ] = target_weight
                        validators_observed.add(target_validator)
                        print("observed", validators_observed)

    """
    def elect_atropos(self):

    def forkless_cause(self):
    
    def communicate_with_neighbors(self):
    """


# Lachesis will eventually run for every node/validator, each of which
# will have a limited view of the test DAG we are using, for now we run
# Lachesis on one node
def process_graph_by_timesteps(graph):
    lachesis_state = Lachesis()
    nodes = iter(
        sorted(graph.nodes(data=True), key=lambda node: node[1]["timestamp"])
    )
    node = next(nodes, None)
    lachesis_state.timestep_graph = nx.DiGraph()  # nodes at the current timestep
    while True:
        if node is None:
            break
        validator = node[0][0]
        timestamp = node[0][1]
        if validator not in lachesis_state.validators:
            lachesis_state.validators.append(validator)
        while timestamp == lachesis_state.time:
            # add node to graph of current nodes and local DAG
            lachesis_state.timestep_graph.add_node(
                (validator, timestamp),
                timestamp=timestamp,
                predecessors=node[1]["predecessors"],
                weight=node[1]["weight"],
                validators_observed=node[1]["validators_observed"],
            )
            lachesis_state.local_dag.add_node(
                (validator, timestamp),
                timestamp=timestamp,
                predecessors=node[1]["predecessors"],
                weight=node[1]["weight"],
                validators_observed=node[1]["validators_observed"],
            )

            # Add edges from this node to its successors
            for successor in graph.successors((validator, timestamp)):
                lachesis_state.local_dag.add_edge((validator, timestamp), successor)

            node = next(nodes, None)
            if node is None:
                break
            validator = node[0][0]
            timestamp = node[0][1]
        else:
            lachesis_state.time += 1
            lachesis_state.timestep_graph = nx.DiGraph()

    G = lachesis_state.local_dag

    print("Nodes in the graph:")
    for node in G.nodes(data=True):
        print(node)

    print("Edges in the graph:")
    for edge in G.edges():
        print(edge)


if __name__ == "__main__":
    # graph = G
    G = dag.convert_input_to_DAG("inputs/graphs/graph_10.txt")
    process_graph_by_timesteps(G)

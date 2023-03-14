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
        self.weight = 0
        self.validator_weights = {}
        self.adjacency_matrix = []
        self.time = 0
        self.last_frame_update_time = 0
        self.global_vector = []
        self.events_at_step = []
        # combining DAGs will eventually be required
        self.local_dag = nx.DiGraph()
        # self.local_rich_dag - DAG with rich logging (block, frame, etc.) for events
        self.timestep_graph = (
            None  # - gDAG nodes at any given concurrent logical timestep
        )

    def quorum(self):
        return (
            sum([self.validator_weights[x] for x in self.validator_weights]) * 2 / 3
        )

    # highest events observed by event algorithm:
    # (validator, frame number): sequence (predecessor count) is the key: value pair
    # successor = direct child

    def highest_events_observed_by_event(self, node):
        direct_child = None
        for (parent, child) in node.out_edges():
            if child[0][0] == node[0][0]:
                direct_child = child
                break

        node.highest_events_observed_by_event = (
            direct_child.highest_events_observed_by_event if direct_child else {}
        )

        for (node, target) in node.out_edges():

            t_events = target.highest_events_observed_by_event
            for (key, value) in t_events.items():
                if key not in node.highest_events_observed_by_event:
                    node.highest_events_observed_by_event[key] = value
                elif value > node.highest_events_observed_by_event[key]:
                    node.highest_events_observed_by_event[key] = value

            node.highest_events_observed_by_event[target] = target.predecessor_count

    def lowest_events_which_observe_event(self, node):
        # source == node; nodes are validators and vice versa

        for (node, target) in node.out_edges():

            t_events = target.lowest_events_which_observe_event

            for (key, value) in t_events.items():
                if key not in node.highest_events_observed_by_event:
                    node.highest_events_observed_by_event[key] = value
                elif value < node.highest_events_observed_by_event[key]:
                    node.highest_events_observed_by_event[key] = value

            if (
                target not in target.lowest_events_which_observe_event
                or (node, self.frame)
                not in target.lowest_events_which_observe_event[target]
            ):
                target.lowest_events_which_observe_event[
                    (node, self.frame)
                ] = node.predecessor_count
            elif (
                node.predecessor_count
                < target.lowest_events_which_observe_event[(node, self.frame)]
            ):
                target.lowest_events_which_observe_event[
                    (node, self.frame)
                ] = node.predecessor_count

    def check_for_roots(self):
        for node in self.timestep_graph.nodes(data=True):
            validator, timestamp = node[0]
            dag_node = self.local_dag.nodes.get((validator, timestamp))

            if dag_node["predecessors"] == 0:
                if self.frame not in self.root_sets:
                    self.root_sets[self.frame] = set(validator)
                else:
                    self.root_sets[self.frame].add(validator)

                # Assign the root property to the node and store it in local_dag
                dag_node["root"] = True
                self.local_dag.nodes[(validator, timestamp)]["root"] = True

        print(self.time, self.root_sets)

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
            lachesis_state.validator_weights[validator] = node[1]["weight"]
        while timestamp == lachesis_state.time:
            # add node to graph of current nodes and local DAG
            lachesis_state.timestep_graph.add_node(
                (validator, timestamp),
                timestamp=timestamp,
                predecessors=node[1]["predecessors"],
                weight=node[1]["weight"],
                lowest_events_which_observe_event={},
                highest_events_observed_by_event={},
            )
            lachesis_state.local_dag.add_node(
                (validator, timestamp),
                timestamp=timestamp,
                predecessors=node[1]["predecessors"],
                weight=node[1]["weight"],
                lowest_events_which_observe_event={},
                highest_events_observed_by_event={},
            )

            # Add edges from this node to its successors
            for successor in graph.successors((validator, timestamp)):
                lachesis_state.local_dag.add_edge((validator, timestamp), successor)

            node = next(nodes, None)
            if node is None:
                break
            validator = node[0][0]
            timestamp = node[0][1]

            if validator not in lachesis_state.validators:
                lachesis_state.validators.append(validator)
                lachesis_state.validator_weights[validator] = node[1]["weight"]

        lachesis_state.check_for_roots()
        lachesis_state.time += 1
        lachesis_state.timestep_graph = nx.DiGraph()

    # G = lachesis_state.local_dag

    """
    print("Nodes in the graph:")
    for node in G.nodes(data=True):
        print(node)

    print("Edges in the graph")
    for edge in G.edges():
        print(edge)
    """


if __name__ == "__main__":
    # graph = G
    G = dag.convert_input_to_DAG("inputs/graphs/graph_10.txt")
    process_graph_by_timesteps(G)

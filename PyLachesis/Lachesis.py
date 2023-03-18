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
        self.frame = 0
        self.root_sets = {}  # {root_set[i] => roots} for i in range(frame_numbers)
        self.cheater_list = set()
        self.validators = []
        self.validator_weights = {}
        self.adjacency_matrix = []
        self.time = 0
        self.local_dag = nx.DiGraph()
        self.timestep_nodes = []

    def quorum(self, frame_number):
        return 2 * sum([self.validator_weights[x] for x in self.root_sets[frame_number]]) // 3 + 1

    def highest_events_observed_by_event(self, node):
        direct_child = None
        for (_, child) in self.local_dag.out_edges(node[0]):
            if child[0] == node[0][0]:
                direct_child = (child, self.local_dag.nodes.get(child))
                break

        node[1]["highest_events_observed_by_event"] = (
            direct_child[1]["highest_events_observed_by_event"] if direct_child else {}
        )

        for (node, target) in self.local_dag.out_edges(node[0]):

            node = (node, self.local_dag.nodes.get(node))
            target = (target, self.local_dag.nodes.get(target))

            t_events = target[1]["highest_events_observed_by_event"]
            for (key, value) in t_events.items():

                if (
                    key not in node[1]["highest_events_observed_by_event"]
                    or value > node[1]["highest_events_observed_by_event"][key]
                ):
                    node[1]["highest_events_observed_by_event"][key] = value

            node[1]["highest_events_observed_by_event"][(target[0][0], self.frame)] = target[1]["predecessors"]

    def lowest_events_which_observe_event(self, node):
        for (source, target) in self.local_dag.out_edges(node[0]):
            target = (target, self.local_dag.nodes.get(target))
            source = (source, self.local_dag.nodes.get(source))

            # updates the target
            if target[0][0] not in target[1]["lowest_events_which_observe_event"]:
                target[1]["lowest_events_which_observe_event"][target[0][0]] = {}
            if (node[0][0], self.frame) not in target[1]["lowest_events_which_observe_event"][target[0][0]] or node[1][
                "predecessors"
            ] < target[1]["lowest_events_which_observe_event"][target[0][0]][(node[0][0], self.frame)]:
                target[1]["lowest_events_which_observe_event"][target[0][0]][(node[0][0], self.frame)] = node[1][
                    "predecessors"
                ]

            # updates the source
            t_events = target[1]["lowest_events_which_observe_event"]
            for (key, value) in t_events.copy().items():
                if key not in source[1]["lowest_events_which_observe_event"]:
                    source[1]["lowest_events_which_observe_event"][key] = value
                else:
                    # vfp = validator and frame pair
                    # seq = sequence number
                    for (vfp, seq) in value.items():
                        if (
                            vfp not in source[1]["lowest_events_which_observe_event"][key]
                            or source[1]["lowest_events_which_observe_event"][key][vfp] < seq
                        ):
                            source[1]["lowest_events_which_observe_event"][key][vfp] = seq

    def expel_cheaters(self, node):
        observed_validators = set()
        for (source, target) in self.local_dag.out_edges(node[0]):
            if target[0][0] not in observed_validators:
                observed_validators.add(target[0][0])
            else:
                self.cheater_list.add(target[0][0])
                # self.root_sets[self.frame].remove(target[0][0])
                remaining_frames = self.frame
                while remaining_frames >= 0:
                    if target[0][0] in self.root_sets[remaining_frames]:
                        self.root_sets[remaining_frames].remove(target[0][0])
                    remaining_frames -= 1

    def check_for_roots(self):

        update_frame = False
        new_root_set = []

        for node in self.timestep_nodes:
            validator, timestamp = node[0]

            if node[1]["predecessors"] == 0:
                if self.frame not in self.root_sets:
                    self.root_sets[self.frame] = set(validator)
                else:
                    self.root_sets[self.frame].add(validator)

                # Assign the root property to the node and store it in local_dag
                self.local_dag.nodes[(validator, timestamp)]["root"] = True

            """
            #NOTE: The following is an assumption

            The strict definition of a root states that it is either:
            - The first event of a validator
            - An event, which is forkless caused by the previous frame roots' quorum

            This function assumes a validator is allowed to be re-introduced if it 
            was "offline" for a few frames
            """
            if (
                self.frame > 0
                and validator not in self.root_sets[self.frame - 1] | self.root_sets[self.frame] | self.cheater_list
            ):
                self.root_sets[self.frame].add(validator)

            self.expel_cheaters(node)
            self.highest_events_observed_by_event(node)
            self.lowest_events_which_observe_event(node)

            for (source, target) in self.local_dag.out_edges(node[0]):
                target = (target, self.local_dag.nodes.get(target))
                source = (source, self.local_dag.nodes.get(source))

                node_weight = 0

                # validator and frame pair = vfp
                for vfp in target[1]["highest_events_observed_by_event"]:
                    frame = vfp[1]
                    val = vfp[0]

                    current_frame_check = (
                        True
                        if frame == self.frame
                        and target[0][0] in self.root_sets[self.frame]
                        and val in self.root_sets[self.frame]
                        else False
                    )

                    last_frame_check = (
                        True
                        if frame == self.frame - 1
                        and target[0][0] in self.root_sets[self.frame - 1]
                        and not target[0][0] in self.root_sets[self.frame]
                        and val in self.root_sets[self.frame - 1]
                        else False
                    )

                    if (current_frame_check or last_frame_check) and not self.local_dag.nodes[target[0]]["root"]:
                        highest_seq = target[1]["highest_events_observed_by_event"][vfp]
                        if (
                            val in target[1]["lowest_events_which_observe_event"]
                            and vfp in target[1]["lowest_events_which_observe_event"][val]
                            and highest_seq >= target[1]["lowest_events_which_observe_event"][val][vfp]
                        ):

                            node_weight += self.validator_weights[val]

                        quorum = self.quorum(self.frame) if current_frame_check else self.quorum(self.frame - 1)

                        if node_weight >= quorum:

                            self.local_dag.nodes[target[0]]["root"] = True

                            """
                            print("self.frame:", self.frame)
                            print("val", val)
                            print("vfp", vfp)
                            print("current root_set", self.root_sets[self.frame])
                            print(
                                "old root_set",
                                self.root_sets[self.frame - 1]
                                if self.frame - 1 in self.root_sets
                                else "",
                            )
                            print("node_weight", node_weight)
                            print("target[0]", target[0])
                            print("target", target)
                            print("frame", frame, vfp[1])
                            print()
                            """

                            if target[0][0] in self.root_sets[self.frame]:
                                update_frame = True
                                new_root_set.append(target)
                            else:
                                self.root_sets[self.frame].add(target[0][0])

        if update_frame:
            self.frame += 1
            self.root_sets[self.frame] = set()
            for root in new_root_set:
                self.root_sets[self.frame].add(root[0][0])

        print(self.time, self.root_sets)

    """
    NOTE: to-do list:

    -optimize data structures for VFPs/etc. to include another nested dictionary
    -write function to graph results
    -elect atropos
    -communicate with others nodes
    """


# Lachesis will eventually run for every node/validator, each of which
# will have a limited view of the test DAG we are using, for now we run
# Lachesis on one node
def process_graph_by_timesteps(graph):
    lachesis_state = Lachesis()
    nodes = iter(sorted(graph.nodes(data=True), key=lambda node: node[1]["timestamp"]))
    node = next(nodes, None)
    lachesis_state.timestep_nodes = []  # nodes at the current timestep
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
            lachesis_state.timestep_nodes.append(
                (
                    (validator, timestamp),
                    {
                        "timestamp": timestamp,
                        "predecessors": node[1]["predecessors"],
                        "weight": node[1]["weight"],
                        "lowest_events_which_observe_event": {},
                        "highest_events_observed_by_event": {},
                        "root": False,
                        "cheater": False,
                    },
                )
            )
            lachesis_state.local_dag.add_node(
                (validator, timestamp),
                timestamp=timestamp,
                predecessors=node[1]["predecessors"],
                weight=node[1]["weight"],
                lowest_events_which_observe_event={},
                highest_events_observed_by_event={},
                root=False,
                cheater=False,
            )
            successors = graph.successors((validator, timestamp))
            for successor in successors:
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
        # print(lachesis_state.timestep_nodes)
        lachesis_state.time += 1
        print()
        lachesis_state.timestep_nodes = []

    G = lachesis_state.local_dag

    # print("Nodes in the graph:")
    # for node in G.nodes(data=True):
    #     print(node[0])
    #     print(node[1])
    #     print()

    """
    print("Edges in the graph")
    for edge in G.edges():
        print(edge)
    """


if __name__ == "__main__":
    # graph = G
    G = dag.convert_input_to_DAG("inputs/graphs/graph_64.txt")
    process_graph_by_timesteps(G)

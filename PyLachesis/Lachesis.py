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
        self.root_set_validators = {}  # {root_set[i] => roots} for i in range(frame_numbers)
        self.root_set_nodes = {}
        self.election_votes = {}
        self.frame_to_decide = 0
        self.cheater_list = set()
        self.validators = set()
        self.validator_weights = {}
        self.adjacency_matrix = []
        self.time = 0
        self.local_dag = nx.DiGraph()
        self.timestep_nodes = []

    def quorum(self, frame_number):
        return 2 * sum([self.validator_weights[x] for x in self.root_set_validators[frame_number]]) // 3 + 1

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
            # efficency boost as all older nodes are irrelevant
            t_events = {k: v for (k, v) in t_events.items() if k[1] >= self.frame - 1}
            for (key, value) in t_events.items():

                if (
                    key not in node[1]["highest_events_observed_by_event"]
                    or value > node[1]["highest_events_observed_by_event"][key]
                ):
                    node[1]["highest_events_observed_by_event"][key] = value

            node[1]["highest_events_observed_by_event"][(target[0][0], self.frame)] = target[1]["predecessors"]

    def lowest_events_which_observe_event(self, node):
        """
        Efficiency boost instead of using another nested dictionary
        to convert validator => (validator, frame) => sequence to
        validator => frame => validator => sequence, as this makes
        the code very hard to read and debug:

        -compute last frame at which all validators have been present
        -ensure that nodes in subsequent frames drop data of those finalized frames
        """
        i = self.frame
        while i > 0 and len(self.root_set_validators[i]) != len(self.validators):
            i -= 1

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

            filtered_t_events = {
                validator: {vfp: sequence for vfp, sequence in frame_dict.items() if vfp[1] >= i}
                for validator, frame_dict in t_events.items()
            }

            for (key, value) in filtered_t_events.items():
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
            if target[0] not in observed_validators:
                observed_validators.add(target[0])
            else:
                self.cheater_list.add(target[0])
                if target[0] in self.validators:
                    self.validators.remove(target[0])
                # self.root_set_validators[self.frame].remove(target[0][0])
                remaining_frames = self.frame
                while remaining_frames >= 0:
                    if target[0] in self.root_set_validators[remaining_frames]:
                        self.root_set_validators[remaining_frames].remove(target[0])

                    self.root_set_nodes[remaining_frames] = {
                        (x, y) for (x, y) in self.root_set_nodes[remaining_frames] if x != target[0]
                    }

                    remaining_frames -= 1

    def forkless_caused(self, validator, candidate_node, frame):

        if (
            validator not in candidate_node[1]["lowest_events_which_observe_event"]
            or (validator, frame) not in candidate_node[1]["highest_events_observed_by_event"]
            or (validator, frame) not in candidate_node[1]["lowest_events_which_observe_event"][validator]
        ):
            return False

        a = candidate_node[1]["highest_events_observed_by_event"][(validator, frame)]
        b = candidate_node[1]["lowest_events_which_observe_event"][validator][(validator, frame)]

        # the no fork condition is implicit as cheaters are expelled
        if a >= b and b != 0:
            return True

    def elect_atropos(self):

        for r in range(self.frame_to_decide + 1, self.frame + 1):
            election_round = r - self.frame_to_decide
            candidates = self.root_set_nodes[self.frame_to_decide]

            if election_round == 1:
                new_roots = self.root_set_nodes[r]
                for root in new_roots:
                    for candidate in candidates:
                        candidate_node = (candidate, self.local_dag.nodes.get(candidate))
                        # vote yes for the candidate if newRoot forkless causes it
                        self.election_votes[(root, candidate)] = {
                            "yes": self.forkless_caused(root[0], candidate_node, self.frame_to_decide),
                            "decided": False,
                        }

    def check_for_roots(self):

        update_frame = False
        new_root_set = []

        for node in self.timestep_nodes:
            validator, timestamp = node[0]

            if node[1]["predecessors"] == 0:
                if self.frame not in self.root_set_validators:
                    self.root_set_validators[self.frame] = set(validator)
                    self.root_set_nodes[self.frame] = set()
                    self.root_set_nodes[self.frame].add(node[0])
                else:
                    self.root_set_validators[self.frame].add(validator)
                    self.root_set_nodes[self.frame].add(node[0])

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
                and validator
                not in self.root_set_validators[self.frame - 1]
                | self.root_set_validators[self.frame]
                | self.cheater_list
            ):
                self.root_set_validators[self.frame].add(validator)
                self.root_set_nodes[self.frame].add(node[0])

            self.expel_cheaters(node)
            self.highest_events_observed_by_event(node)
            self.lowest_events_which_observe_event(node)

            for (source, target) in self.local_dag.out_edges(node[0]):
                target = (target, self.local_dag.nodes.get(target))
                source = (source, self.local_dag.nodes.get(source))

                node_weight_current_frame = 0
                node_weight_last_frame = 0

                # validator and frame pair = vfp
                for vfp in target[1]["highest_events_observed_by_event"]:
                    frame = vfp[1]
                    val = vfp[0]

                    current_frame_check = (
                        True
                        if frame == self.frame
                        and target[0][0] in self.root_set_validators[self.frame]
                        and val in self.root_set_validators[self.frame]
                        else False
                    )

                    last_frame_check = (
                        True
                        if frame == self.frame - 1
                        and target[0][0] in self.root_set_validators[self.frame - 1]
                        and not target[0][0] in self.root_set_validators[self.frame]
                        and val in self.root_set_validators[self.frame - 1]
                        else False
                    )

                    if (current_frame_check or last_frame_check) and not self.local_dag.nodes[target[0]]["root"]:

                        if self.forkless_caused(val, target, frame):
                            if current_frame_check:
                                node_weight_current_frame += self.validator_weights[val]
                            else:
                                node_weight_last_frame += self.validator_weights[val]

                        quorum = (
                            node_weight_last_frame >= self.quorum(self.frame - 1)
                            if last_frame_check
                            else node_weight_current_frame >= self.quorum(self.frame)
                        )

                        if quorum:

                            self.local_dag.nodes[target[0]]["root"] = True

                            if target[0][0] in self.root_set_validators[self.frame]:
                                update_frame = True
                                new_root_set.append(target)
                            else:
                                self.root_set_validators[self.frame].add(target[0][0])
                                self.root_set_nodes[self.frame].add(target[0])

        if update_frame:
            self.frame += 1
            self.root_set_validators[self.frame] = set()
            self.root_set_nodes[self.frame] = set()
            for root in new_root_set:
                self.root_set_validators[self.frame].add(root[0][0])
                self.root_set_nodes[self.frame].add(root[0])

        print(self.time, self.root_set_validators)

    """
    NOTE: to-do list:

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
        if validator not in lachesis_state.validators and validator not in lachesis_state.cheater_list:
            lachesis_state.validators.add(validator)
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
            if validator not in lachesis_state.validators and validator not in lachesis_state.cheater_list:
                lachesis_state.validators.add(validator)
                lachesis_state.validator_weights[validator] = node[1]["weight"]
        lachesis_state.check_for_roots()
        lachesis_state.elect_atropos()
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

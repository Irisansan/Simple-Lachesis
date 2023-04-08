from input_to_dag import convert_input_to_DAG
from sortedcontainers import SortedSet
from collections import deque
from tqdm import tqdm
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import networkx as nx
import glob
import os


class Event:
    def __init__(self, id, seq, creator, parents, frame=None):
        self.id = id
        self.seq = seq
        self.creator = creator
        self.parents = parents
        self.lowest_events_vector = {}
        self.highest_events_observed_by_event = {}
        self.frame = frame


class Lachesis:
    def __init__(self, validator=None):
        self.frame = 1
        self.block = 1
        self.epoch = 1
        self.root_set_validators = {}
        self.root_set_nodes = {}
        self.election_votes = {}
        self.frame_to_decide = 1
        self.cheater_list = set()
        self.validators = set()
        self.validator_weights = {}
        self.time = 0
        self.local_dag = nx.DiGraph()
        self.timestep_nodes = []
        self.decided_roots = {}
        self.atropos_roots = {}

    def quorum(self, frame_number):
        return (
            2
            * sum(
                [
                    self.validator_weights[x]
                    for x in self.root_set_validators[frame_number]
                ]
            )
            // 3
            + 1
        )

    def highest_events_observed_by_event(self, node):
        direct_parent = None
        for parent_id in node.parents:
            parent = self.local_dag.nodes[parent_id]["event"]
            if parent.creator == node.creator:
                direct_parent = parent
                break

        node.highest_events_observed_by_event = (
            direct_parent.highest_events_observed_by_event.copy()
            if direct_parent
            else {}
        )

        for target_id in node.parents:
            target = self.local_dag.nodes[target_id]["event"]

            if (
                (target.creator, target.seq)
                not in node.highest_events_observed_by_event
                or target.seq > node.highest_events_observed_by_event[target.creator]
            ):
                node.highest_events_observed_by_event[target.creator] = target.seq

    def detect_forks(self, event):
        for parent_id in event.parents:
            parent = self.local_dag.nodes[parent_id]["event"]
            if parent.creator == event.creator and parent.seq == event.seq:
                self.cheater_list.add(event.creator)
                self.validator_weights[event.creator] = 0
                break

    def forkless_cause(self, event_a, event_b):
        if event_a.id[0] in self.cheater_list or event_b.id[0] in self.cheater_list:
            return False

        a = event_a.highest_events_observed_by_event
        b = event_b.lowest_events_vector

        yes = 0
        for validator, seq in a.items():
            if validator in b and b[validator]["seq"] <= seq:
                yes += self.validator_weights[validator]

        return yes > self.quorum(self.frame)

    def set_lowest_events_vector(self, event):
        self.lowest_events_vector = {}
        parents = deque(event.parents)

        while parents:
            parent_id = parents.popleft()
            parent = self.local_dag.nodes[parent_id]["event"]
            parent_vector = parent.lowest_events_vector

            if event.creator not in parent_vector:
                parent_vector[event.creator] = {"event_id": event.id, "seq": event.seq}

                if parent.creator != event.creator:
                    parents.extend(parent.parents)

    def check_for_roots(self, event):
        if event.seq == 1:
            return True, 1
        else:
            frame_to_add = None
            if (self.frame == 1 and self.time >= 3) or (
                self.frame > 1
                and len(self.root_set_validators[self.frame])
                >= len(self.root_set_validators[self.frame - 1])
                and event.creator in self.root_set_validators[self.frame]
            ):
                forkless_cause_current_frame = self.forkless_cause_quorum(
                    event, self.quorum(self.frame), self.frame
                )
                if forkless_cause_current_frame:
                    frame_to_add = self.frame + 1
            elif (
                self.frame > 1
                and event.creator not in self.root_set_validators[self.frame]
            ):
                forkless_cause_previous_frame = self.forkless_cause_quorum(
                    event, self.quorum(self.frame - 1), self.frame - 1
                )
                if forkless_cause_previous_frame:
                    frame_to_add = self.frame

            if frame_to_add is not None:
                return True, frame_to_add
            return False, None

    def process_event(self, event, node):
        self.highest_events_observed_by_event(event)
        self.set_lowest_events_vector(event)
        self.detect_forks(event)

        is_root, target_frame = self.check_for_roots(event)
        if is_root:
            if target_frame not in self.root_set_validators:
                self.root_set_validators[target_frame] = SortedSet()
            if target_frame not in self.root_set_nodes:
                self.root_set_nodes[target_frame] = SortedSet()

            self.frame = target_frame

            if self.frame not in self.root_set_validators:
                self.root_set_validators[self.frame] = SortedSet()
            if self.frame not in self.root_set_nodes:
                self.root_set_nodes[self.frame] = SortedSet()

            self.root_set_validators[target_frame].add(event.creator)
            self.root_set_nodes[target_frame].add(event.id)

            self.atropos_voting(event.id)

        if is_root:
            event.frame = target_frame
        else:
            direct_child_seq = event.seq - 1
            direct_child = self.local_dag.nodes.get(
                (event.creator, direct_child_seq), None
            )
            if direct_child:
                event.frame = direct_child["event"].frame
            else:
                event.frame = 1  # Default frame if direct child not found

    def forkless_cause_quorum(self, event, quorum, frame_number):
        forkless_cause_count = 0
        current_frame_roots = self.root_set_nodes[frame_number]

        for root in current_frame_roots:
            root_event = self.local_dag.nodes[root]["event"]
            if self.forkless_cause(event, root_event):
                forkless_cause_count += self.validator_weights[root_event.creator]

        return forkless_cause_count >= quorum

    def atropos_voting(self, new_root):
        candidates = self.root_set_nodes[self.frame_to_decide]
        for candidate in candidates:
            if self.frame_to_decide not in self.election_votes:
                self.election_votes[self.frame_to_decide] = {}
            if (new_root, candidate) not in self.election_votes[self.frame_to_decide]:
                vote = None
                if self.frame == self.frame_to_decide + 1:
                    vote = {
                        "decided": False,
                        "yes": self.forkless_cause(
                            self.local_dag.nodes[new_root]["event"],
                            self.local_dag.nodes[candidate]["event"],
                        ),
                    }
                elif self.frame >= self.frame_to_decide + 2:
                    yes_votes = 0
                    no_votes = 0
                    for prev_root in self.root_set_nodes[self.frame - 1]:
                        prev_vote = self.election_votes[self.frame_to_decide].get(
                            (prev_root, candidate), {"yes": False}
                        )
                        if prev_vote["yes"]:
                            yes_votes += self.validator_weights[prev_root[0]]
                        else:
                            no_votes += self.validator_weights[prev_root[0]]

                    vote = {
                        "decided": yes_votes >= self.quorum(self.frame)
                        or no_votes >= self.quorum(self.frame),
                        "yes": yes_votes >= no_votes,
                    }

                if vote is not None:
                    self.election_votes[self.frame_to_decide][
                        (new_root, candidate)
                    ] = vote
                    if vote["decided"]:
                        self.decided_roots[candidate] = vote
                        if vote["yes"]:
                            self.atropos_roots[self.frame_to_decide] = candidate
                            self.frame_to_decide += 1
                            self.block += 1

    def process_graph_by_timesteps(self, graph):
        nodes = sorted(graph.nodes(data=True), key=lambda node: node[1]["timestamp"])
        max_timestamp = max([node[1]["timestamp"] for node in nodes])

        for current_time in range(max_timestamp + 1):
            nodes_to_process = [
                node for node in nodes if node[1]["timestamp"] == current_time
            ]

            for node in nodes_to_process:
                validator = node[0][0]
                timestamp = node[0][1]
                seq = node[1]["predecessors"]

                if validator not in self.validators:
                    self.validators.add(validator)
                    self.validator_weights[validator] = node[1]["weight"]

                event = Event(
                    id=(validator, seq),
                    seq=seq,
                    creator=validator,
                    parents=[
                        (parent[0], graph.nodes[parent]["predecessors"])
                        for parent in graph.successors((validator, timestamp))
                    ],
                )

                self.local_dag.add_node(
                    (validator, seq),
                    event=event,
                    timestamp=timestamp,
                )

                self.process_event(event, node)

                successors = graph.successors((validator, timestamp))
                for successor in successors:
                    successor_seq = graph.nodes.get(successor)["predecessors"]
                    self.local_dag.add_edge(
                        (validator, seq), (successor[0], successor_seq)
                    )

            self.time += 1

        return self

    def darken_color(color, darken_factor):
        r, g, b = color
        r = int(r * darken_factor)
        g = int(g * darken_factor)
        b = int(b * darken_factor)
        return (r, g, b)

    def graph_results(self, output_filename):
        colors = ["orange", "yellow", "blue", "cyan", "purple"]

        colors_rgb = [mcolors.to_rgb(color) for color in colors]

        darker_colors = []
        for color in colors_rgb:
            darker_color = tuple(c * 0.8 for c in color)
            darker_colors.append(darker_color)

        root_set_nodes_new = {}
        for key, values in self.root_set_nodes.items():
            for v in values:
                validator, seq = v
                timestamp = self.local_dag.nodes[v]["timestamp"]
                root_set_nodes_new[(validator, timestamp)] = key

        atropos_roots_new = {}
        for key, value in self.atropos_roots.items():
            validator, seq = value
            timestamp = self.local_dag.nodes[value]["timestamp"]
            atropos_roots_new[(validator, timestamp)] = key

        atropos_colors = ["limegreen", "green"]

        timestamp_dag = nx.DiGraph()

        for node, data in self.local_dag.nodes(data=True):
            validator, seq = node
            timestamp = data["timestamp"]
            frame = data["event"].frame
            timestamp_dag.add_node((validator, timestamp), seq=seq, frame=frame, **data)

        for src, dest in self.local_dag.edges:
            timestamp_dag.add_edge(
                (src[0], self.local_dag.nodes[src]["timestamp"]),
                (dest[0], self.local_dag.nodes[dest]["timestamp"]),
            )

        node_colors = {}
        for node in timestamp_dag.nodes:
            frame = timestamp_dag.nodes[node]["frame"]
            node_colors[node] = colors[frame % len(colors)]
            if node in root_set_nodes_new:
                node_colors[node] = darker_colors[root_set_nodes_new[node] % 5]
            if node in atropos_roots_new:
                node_colors[node] = atropos_colors[atropos_roots_new[node] % 2]

        pos = {}
        num_nodes = len(self.validator_weights)
        num_levels = max([node[1] for node in timestamp_dag.nodes])

        figsize = [20, 10]
        if num_levels >= 15:
            figsize[0] = figsize[0] * num_levels / 20
        if num_nodes >= 10:
            figsize[0] = figsize[0] * num_nodes / 4
            figsize[1] = figsize[1] * num_nodes / 10

        fig = plt.figure(figsize=(figsize[0], figsize[1]))
        for i in range(num_nodes + 25):
            for j in range(num_levels + 25):
                node = (chr(i + 65), j)
                pos[node] = (j, i)

        labels = {
            (chr(i + 65), j): (
                chr(i + 65),
                j,
                timestamp_dag.nodes.get((chr(i + 65), j), {}).get("seq"),
            )
            for i in range(num_nodes)
            for j in range(num_levels + 1)
            if (chr(i + 65), j) in timestamp_dag.nodes
        }

        nx.draw(
            timestamp_dag,
            pos,
            with_labels=True,
            labels={
                val: r"$\mathrm{{{}}}_{{{},{}}}$".format(
                    labels[val][0], labels[val][1], labels[val][2]
                )
                for val in labels
            },
            font_family="serif",
            font_size=9,
            node_size=900,
            node_color=[
                node_colors.get(node, node_colors[node])
                for node in timestamp_dag.nodes()
            ],
            font_weight="bold",
        )

        fig.savefig(
            output_filename + ".pdf", format="pdf", dpi=300, bbox_inches="tight"
        )
        plt.close()

    def run_lachesis(self, graph_file, output_file):
        G = convert_input_to_DAG(graph_file)
        self.process_graph_by_timesteps(G)
        self.graph_results(output_file)

        return {
            "graph": graph_file,
            "atropos_roots": self.atropos_roots,
            "frame": self.frame,
            "block": self.block,
            "frame_to_decide": self.frame_to_decide,
            "root_set_nodes": self.root_set_nodes,
            "root_set_validators": self.root_set_validators,
            "election_votes": self.election_votes,
        }


if __name__ == "__main__":
    input_graphs_directory = "../inputs/graphs/graph_*.txt"
    file_list = glob.glob(input_graphs_directory)

    print("file count", len(file_list))

    for i, input_filename in tqdm(
        enumerate(file_list), total=len(file_list), desc="Processing files"
    ):
        base_filename = os.path.basename(input_filename)
        graph_name = base_filename[
            base_filename.index("_") + 1 : base_filename.index(".txt")
        ]
        output_filename = f"../inputs/results/result_{graph_name}"
        lachesis_state = Lachesis()
        lachesis_state.run_lachesis(input_filename, output_filename)

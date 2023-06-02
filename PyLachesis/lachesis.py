import random
from sortedcontainers import SortedSet
from collections import deque
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import networkx as nx


def convert_input_to_DAG(input_file):
    nodes = []

    with open(input_file, "r") as f:
        for line in f:
            line = line.strip()
            parts = line.split(";")

            node_info = parts[0].strip()[6:-1]
            node_id, timestamp, predecessors = node_info.split(",")
            timestamp, predecessors = int(timestamp), int(predecessors)
            node_key = (node_id[1:], predecessors)

            node = Node(node_key, timestamp, predecessors)
            nodes.append(node)

            for child_info in parts[1:]:
                child_info = child_info.strip()[7:-1]
                child_info_parts = child_info.split(",")
                if len(child_info_parts) < 2:
                    continue
                child_id, child_timestamp = child_info_parts[:2]
                child_timestamp = int(child_timestamp)
                child_predecessors = int(child_info_parts[2])
                child_key = (child_id[1:], child_predecessors)

                child = Node(child_key, child_timestamp, child_predecessors)
                node.children.append(child)

    return nodes


class LachesisMultiInstance:
    def __init__(self):
        self.instances = {}
        self.nodes = []
        self.seen_validators = set()
        self.base_validator = Lachesis()

    def initialize_instances(self, validators, weights):
        for validator in validators:
            self.instances[validator] = Lachesis(validator)
            self.instances[validator].validators = validators.copy()
            self.instances[validator].initialize_validator_weights(validators, weights)

    def add_validators(self, node):
        validator = node.id[0]
        self.seen_validators.add(validator)
        for instance in self.instances.values():
            if validator not in instance.validators:
                instance.validators.add(validator)
                instance.validator_weights[validator] = node.weight

    def process_graph_by_timesteps(self):
        max_timestamp = max(node.timestamp for node in self.nodes)

        for current_time in range(max_timestamp + 1):
            nodes_to_process = [
                node for node in self.nodes if node.timestamp == current_time
            ]

            random.shuffle(nodes_to_process)

            for node in nodes_to_process:
                validator = node.id[0]
                seq = node.predecessors

                if node.id[0] not in self.seen_validators:
                    self.add_validators(node)

                event = Event(
                    id=(validator, seq),
                    seq=seq,
                    creator=validator,
                    parents=[(parent.id) for parent in node.children],
                )

                instance = self.instances[validator]
                if event.id not in instance.event_timestamps:
                    instance.event_timestamps[event.id] = []
                instance.event_timestamps[event.id].append(current_time)

                event_key = (event.id, current_time)
                if event_key in instance.event_timestamp_parents:
                    instance.event_timestamp_parents[event_key].extend(
                        [(parent.id, parent.timestamp) for parent in node.children]
                    )
                else:
                    instance.event_timestamp_parents[event_key] = [
                        (parent.id, parent.timestamp) for parent in node.children
                    ]

                instance.defer_event_processing(event, current_time, self.instances)

            for instance in self.instances.values():
                instance.process_request_queue(self.instances)

            for instance in self.instances.values():
                instance.process_deferred_events()

            for instance in self.instances.values():
                instance.time += 1

        return self.instances

    def run_lachesis_multi_instance(self, input_file, output_file, create_graph=False):
        nodes = convert_input_to_DAG(input_file)
        self.nodes = nodes

        sorted_nodes = sorted(
            (node for node in nodes if node.timestamp <= 20),
            key=lambda node: node.timestamp,
        )
        validators = [node.id[0] for node in sorted_nodes]
        weights = [node.weight for node in sorted_nodes]

        self.initialize_instances(validators, weights)
        self.process_graph_by_timesteps()

        self.base_validator.process_graph_by_timesteps(self.nodes)
        self.base_validator.lachesis_state = self.base_validator.return_lachesis_state()
        reference_state = self.base_validator.lachesis_state

        for instance in self.instances.values():
            # graphing
            if create_graph:
                output_file_validator = instance.validator + "_" + output_file
                instance.graph_results(output_file_validator)

            # verifying deterministic computation in different validators
            self.lachesis_state = instance.return_lachesis_state()
            instance_state = self.lachesis_state

            try:
                assert instance_state["frame"] <= reference_state["frame"]
                assert instance_state["block"] <= reference_state["block"]
                assert all(
                    [
                        f in reference_state["root_set_validators"]
                        for f in instance_state["root_set_validators"]
                    ]
                )
                assert all(
                    [
                        instance_state["root_set_validators"][f]
                        <= reference_state["root_set_validators"][f]
                        for f in instance_state["root_set_validators"]
                    ]
                )
                assert all(
                    [
                        f in reference_state["root_set_nodes"]
                        for f in instance_state["root_set_nodes"]
                    ]
                )
                assert all(
                    [
                        instance_state["root_set_nodes"][f]
                        <= reference_state["root_set_nodes"][f]
                        for f in instance_state["root_set_nodes"]
                    ]
                )
                assert (
                    instance_state["frame_to_decide"]
                    <= reference_state["frame_to_decide"]
                )
                assert instance_state["cheater_list"] <= reference_state["cheater_list"]
                assert instance_state["time"] <= reference_state["time"]
                assert all(
                    [
                        f in reference_state["atropos_roots"]
                        for f in instance_state["atropos_roots"]
                    ]
                )

                print(reference_state["atropos_roots"])
                print(instance_state["atropos_roots"])
                # assert all(
                #     [
                #         instance_state["atropos_roots"][f]
                #         == reference_state["atropos_roots"][f]
                #         for f in instance_state["atropos_roots"]
                #     ]
                # )

            except Exception as e:
                print("instance:", instance.validator)
                print("lachesis_state:\n", instance_state)
                print()
                print("reference state of base validator:\n", reference_state)
                raise RuntimeError(
                    "Assertion of deterministic computation failed:", str(e)
                )


class Node:
    def __init__(self, id, timestamp, predecessors):
        self.id = id
        self.timestamp = timestamp
        self.predecessors = predecessors
        self.children = []
        self.weight = 1

    def __repr__(self):
        return f"Node({self.id}, {self.timestamp}, {self.predecessors})"


class Event:
    def __init__(
        self,
        id,
        seq,
        creator,
        parents,
        frame=None,
        simultaneous_duplicate=False,
    ):
        self.id = id
        self.seq = seq
        self.creator = creator
        self.parents = parents
        self.lowest_events_vector = {}
        self.highest_events_observed_by_event = {}
        self.frame = frame
        self.simultaneous_duplicate = simultaneous_duplicate

    def copy_basic_properties(self):
        return Event(
            id=self.id,
            seq=self.seq,
            creator=self.creator,
            parents=self.parents,
            simultaneous_duplicate=self.simultaneous_duplicate,
        )


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
        self.validator = validator
        self.validators = set()
        self.validator_weights = {}
        self.time = 0
        self.events = {}
        self.event_timestamps = {}
        self.timestep_nodes = []
        self.decided_roots = {}
        self.atropos_roots = {}
        self.last_validator_sequence = {}
        self.request_queue = deque()
        self.process_queue = {}
        self.quorum_values = {}
        self.next_event_index = {}
        self.event_parents = {}
        self.event_timestamp_indices = {}
        self.event_timestamp_parents = {}
        self.forks = {}
        self.initial_validator_weights = {}
        self.validator_weights = {}
        self.lachesis_state = None

    def initialize_validator_weights(self, validators, weights):
        self.validators = validators
        self.validator_weights = dict(zip(validators, weights))
        self.initial_validator_weights = self.validator_weights.copy()
        self.validator_weights = self.validator_weights.copy()

    def defer_event_processing(self, event, timestamp, instances):
        existing_events = self.process_queue.get(event.id, [])

        if not existing_events:
            self.process_queue[event.id] = [
                {
                    "timestamp": timestamp,
                    "event": event,
                    "parents": self.event_timestamp_parents.get(
                        (event.id, timestamp), []
                    ),
                }
            ]
        else:
            same_timestamp_event_dict = None
            for existing_event_dict in existing_events:
                if existing_event_dict["timestamp"] == timestamp:
                    same_timestamp_event_dict = existing_event_dict
                    break

            if same_timestamp_event_dict:
                same_timestamp_event_dict["event"].parents = list(
                    set(same_timestamp_event_dict["event"].parents).union(
                        set(event.parents)
                    )
                )
                same_timestamp_event_dict["event"].simultaneous_duplicate = True
            else:
                self.process_queue[event.id].append(
                    {
                        "timestamp": timestamp,
                        "event": event,
                        "parents": self.event_timestamp_parents.get(
                            (event.id, timestamp), []
                        ),
                    }
                )

        self.update_request_queue(event, instances)

    def update_request_queue(self, event, instances):
        existing_events = self.process_queue[event.id]

        for event_data in existing_events:
            parent_id_timestamp_list = event_data["parents"]

            for parent_id, parent_timestamp in parent_id_timestamp_list:
                if (
                    not any(
                        (parent_timestamp, parent_id) in parent_event_tuples
                        for parent_event_tuples in self.process_queue.values()
                    )
                    and (parent_id, parent_timestamp)
                    not in self.event_timestamp_parents
                ):
                    parent_instance = instances[parent_id[0]]
                    parent_instance.request_queue.append(
                        (event.creator, [(parent_id, parent_timestamp)])
                    )

    def process_request_queue(self, instances):
        while self.request_queue:
            (
                recipient_id,
                missing_event_id_timestamp_tuples,
            ) = self.request_queue.popleft()

            recipient_instance = instances[recipient_id]
            for event_id, timestamp in missing_event_id_timestamp_tuples:
                if (
                    event_id,
                    timestamp,
                ) not in recipient_instance.event_timestamp_parents:
                    missing_event = self.events[event_id].copy_basic_properties()
                    missing_event.parents = [
                        parent_id
                        for parent_id, _ in self.event_timestamp_parents[
                            (event_id, timestamp)
                        ]
                    ]

                    if event_id not in recipient_instance.process_queue:
                        recipient_instance.process_queue[event_id] = [
                            {
                                "timestamp": timestamp,
                                "event": missing_event,
                                "parents": self.event_timestamp_parents.get(
                                    (event_id, timestamp), []
                                ),
                            }
                        ]
                    else:
                        if not any(
                            existing_event_dict["timestamp"] == timestamp
                            for existing_event_dict in recipient_instance.process_queue[
                                event_id
                            ]
                        ):
                            recipient_instance.process_queue[event_id].append(
                                {
                                    "timestamp": timestamp,
                                    "event": missing_event,
                                    "parents": self.event_timestamp_parents.get(
                                        (event_id, timestamp), []
                                    ),
                                }
                            )

                    parent_id_timestamp_list = self.event_timestamp_parents[
                        (event_id, timestamp)
                    ]

                    for parent_id, parent_timestamp in parent_id_timestamp_list:
                        if (
                            not any(
                                (
                                    existing_event_dict["timestamp"],
                                    existing_event_dict["event"].id,
                                )
                                == (parent_timestamp, parent_id)
                                for existing_event_dicts in recipient_instance.process_queue.values()
                                for existing_event_dict in existing_event_dicts
                            )
                            and (parent_id, parent_timestamp)
                            not in recipient_instance.event_timestamp_parents
                        ):
                            self.request_queue.append(
                                (recipient_id, [(parent_id, parent_timestamp)])
                            )

    def process_deferred_events(self):
        all_event_tuples = []
        for event_id in self.process_queue:
            all_event_tuples.extend(self.process_queue[event_id])

        all_event_tuples.sort(key=lambda x: x["timestamp"])

        for event_data in all_event_tuples:
            timestamp = event_data["timestamp"]
            event = event_data["event"]

            if event.id not in self.event_timestamps:
                self.event_timestamps[event.id] = [timestamp]
            else:
                self.event_timestamps[event.id].append(timestamp)

            self.event_timestamp_parents[(event.id, timestamp)] = event_data["parents"]

            self.process_event(event)

            self.process_queue[event.id].remove(event_data)
            if not self.process_queue[event.id]:
                del self.process_queue[event.id]

    def process_event(self, event):
        self.events[event.id] = event
        fork_detected = self.detect_forks(event)

        if fork_detected:
            if event.creator not in self.forks:
                self.forks[event.creator] = event.seq
            self.validator_weights[event.creator] = 0

        if self.frame not in self.quorum_values:
            self.quorum(self.frame)

        if event.creator not in self.cheater_list:
            self.highest_events_observed_by_event(event)
            self.set_lowest_events_vector(event)

            is_root, target_frame = self.check_for_roots(event)
            if is_root:
                if target_frame not in self.root_set_validators:
                    self.root_set_validators[target_frame] = SortedSet()
                if target_frame not in self.root_set_nodes:
                    self.root_set_nodes[target_frame] = SortedSet()

                event.frame = target_frame

                self.events[event.id].frame = target_frame

                self.frame = target_frame if target_frame > self.frame else self.frame

                if event.creator not in self.cheater_list:
                    self.root_set_validators[target_frame].add(event.creator)
                    self.root_set_nodes[target_frame].add(event.id)

                if self.frame not in self.quorum_values:
                    self.quorum(self.frame)

                self.atropos_voting(event.id)

            else:
                direct_child = self.events[(event.creator, event.seq - 1)]
                event.frame = direct_child.frame

    def detect_forks(self, event):
        fork_detected = False

        parent_ids = event.parents

        if event.simultaneous_duplicate:
            self.cheater_list.add(event.creator)
            self.validator_weights[event.creator] = 0
            fork_detected = True

        if event.id in parent_ids:
            self.cheater_list.add(event.creator)
            self.validator_weights[event.creator] = 0
            fork_detected = True

        validator = event.creator
        seq = event.seq

        if validator not in self.last_validator_sequence:
            self.last_validator_sequence[validator] = seq
        elif self.last_validator_sequence[validator] < seq:
            self.last_validator_sequence[validator] = seq
        else:
            self.cheater_list.add(validator)
            self.validator_weights[validator] = 0
            fork_detected = True

        return fork_detected

    def quorum(self, frame_number):
        if frame_number not in self.quorum_values:
            self.quorum_values[frame_number] = (
                2 * sum(self.validator_weights.values()) // 3 + 1
            )

        return self.quorum_values[frame_number]

    def highest_events_observed_by_event(self, node):
        for parent_id in node.parents:
            parent = self.events[parent_id]

            if (
                parent.creator not in node.highest_events_observed_by_event
                or parent.seq > node.highest_events_observed_by_event[parent.creator]
            ):
                node.highest_events_observed_by_event[parent.creator] = parent.seq

            for creator, seq in parent.highest_events_observed_by_event.items():
                if (
                    creator not in node.highest_events_observed_by_event
                    or seq > node.highest_events_observed_by_event[creator]
                ):
                    node.highest_events_observed_by_event[creator] = seq

    def forkless_cause(self, event_a, event_b):
        if event_a.id[0] in self.cheater_list or event_b.id[0] in self.cheater_list:
            return False

        a = event_a.highest_events_observed_by_event
        b = event_b.lowest_events_vector

        yes = 0
        for validator, seq in a.items():
            if validator in b and b[validator]["seq"] <= seq:
                yes += self.validator_weights[validator]

        return yes >= self.quorum(event_b.frame)

    def set_lowest_events_vector(self, event):
        parents = deque(event.parents)

        while parents:
            parent_id = parents.popleft()
            if parent_id[0] in self.cheater_list:
                continue
            parent = self.events[parent_id]
            parent_vector = parent.lowest_events_vector

            if event.creator not in parent_vector:
                parent_vector[event.creator] = {"event_id": event.id, "seq": event.seq}

                if event.creator != parent.creator:
                    parents.extend(parent.parents)

    def check_for_roots(self, event):
        if event.seq == 1:
            return True, 1
        else:
            direct_child = self.events[(event.creator, event.seq - 1)]

            if event.creator not in self.cheater_list:
                forkless_cause_current_frame = self.forkless_cause_quorum(
                    event, direct_child.frame
                )
                if forkless_cause_current_frame:
                    return True, direct_child.frame + 1

            return False, None

    def forkless_cause_quorum(self, event, frame_number):
        forkless_cause_count = 0
        frame_roots = self.root_set_nodes[frame_number]

        for root in frame_roots:
            root_event = self.events[root]
            if self.forkless_cause(event, root_event):
                forkless_cause_count += self.validator_weights[root_event.creator]

        return forkless_cause_count >= self.quorum(frame_number)

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
                            self.events[new_root],
                            self.events[candidate],
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

    def process_graph_by_timesteps(self, nodes):
        sorted_nodes = sorted(
            (node for node in nodes if node.timestamp <= 10),
            key=lambda node: node.timestamp,
        )
        max_timestamp = max(node.timestamp for node in nodes)

        validators = [node.id[0] for node in sorted_nodes]
        weights = [node.weight for node in sorted_nodes]

        self.initialize_validator_weights(validators, weights)

        for current_time in range(max_timestamp + 1):
            nodes_to_process = [
                node for node in nodes if node.timestamp == current_time
            ]

            random.shuffle(nodes_to_process)

            for node in nodes_to_process:
                validator = node.id[0]
                seq = node.predecessors

                if validator not in self.validators:
                    self.validators.add(validator)
                    self.validator_weights[validator] = node.weight

                event = Event(
                    id=(validator, seq),
                    seq=seq,
                    creator=validator,
                    parents=[(parent.id) for parent in node.children],
                )

                self.events[event.id] = event

                if event.id not in self.event_timestamps:
                    self.event_timestamps[event.id] = []
                self.event_timestamps[event.id].append(current_time)

                self.process_event(event)

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
                timestamp = self.event_timestamps[v][-1]
                root_set_nodes_new[(validator, timestamp)] = key

        atropos_roots_new = {}
        for key, value in self.atropos_roots.items():
            validator, seq = value
            timestamp = self.event_timestamps[value][-1]
            atropos_roots_new[(validator, timestamp)] = key

        atropos_colors = ["limegreen", "green"]

        timestamp_dag = nx.DiGraph()

        for node, data in self.events.items():
            validator, seq = node
            timestamp = self.event_timestamps[node][-1]
            frame = data.frame
            weight = self.validator_weights[validator]
            timestamp_dag.add_node(
                (validator, timestamp), seq=seq, frame=frame, weight=weight
            )
            for parent in data.parents:
                if parent in self.events:
                    parent_timestamp = self.event_timestamps[parent][-1]
                    timestamp_dag.add_edge(
                        (validator, timestamp),
                        (parent[0], parent_timestamp),
                    )

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

        cheater_nodes = [
            (validator, timestamp)
            for validator, timestamp in timestamp_dag.nodes
            if validator in self.cheater_list
        ]
        timestamp_dag.remove_nodes_from(cheater_nodes)

        labels = {
            node: (node[0], node[1], timestamp_dag.nodes[node]["seq"])
            for node in timestamp_dag.nodes
        }

        node_colors = {}
        for node in timestamp_dag.nodes:
            frame = timestamp_dag.nodes[node]["frame"]
            if frame:
                node_colors[node] = colors[frame % len(colors)]
            else:
                node_colors[node] = "black"
            if node in root_set_nodes_new:
                node_colors[node] = darker_colors[root_set_nodes_new[node] % 5]
            if node in atropos_roots_new:
                node_colors[node] = atropos_colors[atropos_roots_new[node] % 2]

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

        fig.savefig(output_filename, format="pdf", dpi=300, bbox_inches="tight")
        plt.close()

    def run_lachesis(self, graph_file, output_file, create_graph=False):
        nodes = convert_input_to_DAG(graph_file)
        self.process_graph_by_timesteps(nodes)
        if create_graph:
            self.graph_results(output_file)
        self.lachesis_state = self.return_lachesis_state()
        # print("base validator")
        # print("lachesis_state:", self.lachesis_state)
        # print()

    def return_lachesis_state(self):
        return {
            "frame": self.frame,
            "block": self.block,
            "root_set_validators": self.root_set_validators,
            "root_set_nodes": self.root_set_nodes,
            "frame_to_decide": self.frame_to_decide,
            "cheater_list": self.cheater_list,
            "time": self.time,
            "atropos_roots": self.atropos_roots,
        }


if __name__ == "__main__":
    lachesis_instance = Lachesis()
    lachesis_instance.run_lachesis(
        "../inputs/graphs_with_cheaters/graph_87.txt", "result.pdf", True
    )

    lachesis_multiinstance = LachesisMultiInstance()
    lachesis_multiinstance.run_lachesis_multi_instance(
        "../inputs/graphs_with_cheaters/graph_87.txt", "result_multiinstance.pdf", True
    )

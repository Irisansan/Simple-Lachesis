import random
import networkx as nx
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from collections import deque
import re


def parse_data(file_path):
    event_list = []

    with open(file_path, "r") as file:
        for line in file:
            # Parse line
            unique_id_match = re.search(r"unique_id:\s([a-z0-9-]*)", line)
            label_match = re.search(r"label:\s\(([\w\s]+),(\d+),(\d+),(\d+)\)", line)
            if not (unique_id_match and label_match):
                continue

            unique_id = unique_id_match.group(1)
            validator, timestamp, sequence, weight = label_match.groups()

            # Create event and add to dictionary
            event = Event(
                validator, int(timestamp), int(sequence), int(weight), unique_id
            )
            event_list.append(event)

            # Add parents if they exist
            child_unique_ids = re.findall(r"child_unique_id:\s([a-z0-9-]*)", line)
            for child_unique_id in child_unique_ids:
                event.add_parent(child_unique_id)

    return event_list


def filter_validators_and_weights(events):
    validators = []
    validator_weights = {}

    for event in events:
        if event.timestamp > 10:
            break
        if event.validator not in validators:
            validators.append(event.validator)
            validator_weights[event.validator] = event.weight

    return validators, validator_weights


class Event:
    def __init__(self, validator, timestamp, sequence, weight, unique_id):
        self.validator = validator
        self.timestamp = timestamp
        self.sequence = sequence
        self.weight = weight
        self.uuid = unique_id
        self.frame = None
        self.root = False
        self.atropos = False
        self.highest_observed = {}
        self.lowest_observing = {}
        self.visited = {}
        self.parents = []
        self.highest_timestamps_observed = {}

    def add_parent(self, parent_uuid):
        self.parents.append(parent_uuid)

    def __repr__(self):
        return f"\nEvent({self.validator}, {self.timestamp}, {self.sequence}, {self.weight}, {self.uuid}, {self.parents}, {self.highest_observed}, {self.lowest_observing})"


class Lachesis:
    def __init__(self):
        self.validator = None
        self.validators = []
        self.validator_weights = {}
        self.time = 1
        self.events = []
        self.frame = 1
        self.epoch = 1
        self.root_set_validators = []
        self.root_set_events = {}
        self.frame_to_decide = None
        self.observed_sequences = {}
        self.validator_cheater_list = {}
        self.decided_roots = []
        self.atropos_roots = []
        self.quorum_cache = {}
        self.uuid_event_dict = {}
        self.suspected_cheaters = set()
        self.confirmed_cheaters = set()
        self.highest_validator_timestamps = {}
        self.election_votes = {}
        self.atropos_roots = {}
        self.decided_roots = {}
        self.block = 1
        self.frame_to_decide = 1

    def initialize_validators(self, validators, validator_weights):
        self.validators = validators
        self.validator_weights = validator_weights

    def quorum(self, frame):
        if frame in self.quorum_cache:
            return self.quorum_cache[frame]
        else:
            weights_total = sum(self.validator_weights.values())

            for cheater in self.suspected_cheaters:
                cheater_observation = 0
                for validator, cheaters in self.validator_cheater_list.items():
                    if cheater in cheaters:
                        cheater_observation += self.validator_weights[validator]
                if cheater_observation >= 2 * weights_total // 3 + 1:
                    self.confirmed_cheaters.add(cheater)
                    weights_total -= self.validator_weights[cheater]
                    self.validator_weights[cheater] = 0

            for validator, timestamp in self.highest_validator_timestamps.items():
                if self.time - timestamp >= 20:
                    # If the validator's highest timestamp is too old, ignore its weight
                    weights_total -= self.validator_weights[validator]
                    self.validator_weights[validator] = 0

            self.quorum_cache[frame] = 2 * weights_total // 3 + 1
            return self.quorum_cache[frame]

    def get_direct_child(self, event):
        direct_child_uuid = next(
            (
                uuid
                for uuid in event.parents
                if self.uuid_event_dict[uuid].sequence == event.sequence - 1
                and self.uuid_event_dict[uuid].validator == event.validator
            ),
            None,
        )
        if direct_child_uuid is not None:
            return self.uuid_event_dict[direct_child_uuid]
        else:
            return None

    def is_root(self, event):
        if event.sequence == 1:
            return True

        direct_child = self.get_direct_child(event)
        if direct_child is None:
            return False

        event.frame = direct_child.frame
        frame_roots = self.root_set_events.get(event.frame, [])
        if not frame_roots:
            return False

        forkless_cause_weights = sum(
            [
                self.validator_weights[root.validator]
                for root in frame_roots
                if self.forkless_cause(event, root)
            ]
        )

        return forkless_cause_weights >= self.quorum(event.frame)

    def set_roots(self, event):
        if self.is_root(event):
            event.root = True
            if event.sequence == 1:
                event.frame = self.frame
            else:
                event.frame += 1
            if self.frame < event.frame:
                self.frame = event.frame
            if event.frame in self.root_set_events:
                self.root_set_events[event.frame].append(event)
            else:
                self.root_set_events[event.frame] = [event]
                # Immediately calculate the quorum for this new frame
                self.quorum(event.frame)
            self.atropos_voting(event)

    def atropos_voting(self, new_root):
        candidates = sorted(
            self.root_set_events[self.frame_to_decide],
            key=lambda event: (
                event.timestamp,
                event.validator,
                event.sequence,
                event.weight,
            ),
        )

        for candidate in candidates:
            if self.frame_to_decide not in self.election_votes:
                self.election_votes[self.frame_to_decide] = {}

            if (new_root.uuid, candidate.uuid) not in self.election_votes[
                self.frame_to_decide
            ]:
                vote = None

                if self.frame == self.frame_to_decide + 1:
                    vote = {
                        "decided": False,
                        "yes": self.forkless_cause(new_root, candidate),
                    }
                elif self.frame >= self.frame_to_decide + 2:
                    yes_votes = 0
                    no_votes = 0

                    for prev_root in sorted(
                        self.root_set_events[self.frame - 1],
                        key=lambda event: (
                            event.timestamp,
                            event.validator,
                            event.sequence,
                            event.weight,
                        ),
                    ):
                        prev_vote = self.election_votes[self.frame_to_decide].get(
                            (prev_root.uuid, candidate.uuid), {"yes": False}
                        )
                        if prev_vote["yes"]:
                            yes_votes += self.validator_weights[prev_root.validator]
                        else:
                            no_votes += self.validator_weights[prev_root.validator]

                    vote = {
                        "decided": yes_votes >= self.quorum(self.frame)
                        or no_votes >= self.quorum(self.frame),
                        "yes": yes_votes > no_votes,
                    }

                if vote is not None:
                    self.election_votes[self.frame_to_decide][
                        (new_root.uuid, candidate.uuid)
                    ] = vote

                    if vote["decided"]:
                        self.decided_roots[candidate.uuid] = vote
                        if vote["yes"]:
                            self.atropos_roots[self.frame_to_decide] = candidate.uuid
                            candidate.atropos = True
                            self.frame_to_decide += 1
                            self.block += 1

    def forkless_cause(self, event_a, event_b):
        if event_a.validator in self.validator_cheater_list.get(
            event_b.validator, set()
        ) or event_b.validator in self.validator_cheater_list.get(
            event_a.validator, set()
        ):
            return False

        a = event_a.highest_observed
        b = event_b.lowest_observing

        yes = 0
        for validator, sequence in a.items():
            if validator in b and b[validator]["sequence"] <= sequence:
                yes += self.validator_weights[validator]

        return yes >= self.quorum(event_b.frame)

    def detect_forks(self, event):
        if event.validator not in self.validator_cheater_list:
            self.validator_cheater_list[event.validator] = set()

        parents = deque(event.parents)

        while parents:
            parent_id = parents.popleft()
            parent = self.uuid_event_dict[parent_id]

            # If the validator of the event is not in the parent vector, add it
            if event.validator not in parent.visited:
                parent.visited[event.validator] = {
                    "uuid": event.uuid,
                    "sequence": event.sequence,
                }

                # Add sequence numbers observed by the event's validator
                if event.validator not in self.observed_sequences:
                    self.observed_sequences[event.validator] = {}
                if parent.validator not in self.observed_sequences[event.validator]:
                    self.observed_sequences[event.validator][parent.validator] = set()

                if (
                    parent.sequence
                    in self.observed_sequences[event.validator][parent.validator]
                ):
                    # The event's validator has observed a fork by the parent validator
                    self.validator_cheater_list[event.validator].add(parent.validator)
                    self.suspected_cheaters.add(parent.validator)
                else:
                    self.observed_sequences[event.validator][parent.validator].add(
                        parent.sequence
                    )
                    parents.extend(parent.parents)

    def set_highest_timestamps_observed(self, event):
        for parent_id in event.parents:
            parent = self.uuid_event_dict[parent_id]

            if (
                parent.validator not in event.highest_timestamps_observed
                or parent.timestamp
                > event.highest_timestamps_observed[parent.validator]
            ):
                event.highest_timestamps_observed[parent.validator] = parent.timestamp

            for validator, timestamp in parent.highest_timestamps_observed.items():
                if (
                    validator not in event.highest_timestamps_observed
                    or timestamp > event.highest_timestamps_observed[validator]
                ):
                    event.highest_timestamps_observed[validator] = timestamp

            # Update the Lachesis attribute
            for validator, timestamp in event.highest_timestamps_observed.items():
                if (
                    validator not in self.highest_validator_timestamps
                    or timestamp > self.highest_validator_timestamps[validator]
                ):
                    self.highest_validator_timestamps[validator] = timestamp

    def set_highest_events_observed(self, event):
        for parent_id in event.parents:
            parent = self.uuid_event_dict[parent_id]

            if (
                parent.validator not in event.highest_observed
                or parent.sequence > event.highest_observed[parent.validator]
            ):
                event.highest_observed[parent.validator] = parent.sequence

            for validator, sequence in parent.highest_observed.items():
                if (
                    validator not in event.highest_observed
                    or sequence > event.highest_observed[validator]
                ):
                    event.highest_observed[validator] = sequence

    def set_lowest_observing_events(self, event):
        parents = deque(event.parents)

        while parents:
            parent_id = parents.popleft()
            parent = self.uuid_event_dict[parent_id]

            if parent.validator in self.validator_cheater_list[event.validator]:
                continue

            # If the validator of the event is not in the parent vector, add it
            if event.validator not in parent.lowest_observing and (
                parent.validator not in self.validator_cheater_list
                or event.validator not in self.validator_cheater_list[event.validator]
            ):
                parent.lowest_observing[event.validator] = {
                    "uuid": event.uuid,
                    "sequence": event.sequence,
                }

                parents.extend(parent.parents)

    def process_events(self, events):
        # Group events by timestamp
        timestamp_event_dict = {}
        for event in events:
            if event.timestamp not in timestamp_event_dict:
                timestamp_event_dict[event.timestamp] = []
            timestamp_event_dict[event.timestamp].append(event)

        # Get the maximum timestamp
        max_timestamp = max(timestamp_event_dict.keys())
        min_timestamp = min(timestamp_event_dict.keys())

        # Process events from timestamp 1 to max_timestamp
        for timestamp in range(min_timestamp, max_timestamp + 1):
            # Retrieve, shuffle and process events with the current timestamp
            current_timestamp_events = timestamp_event_dict.get(timestamp, [])
            random.shuffle(current_timestamp_events)

            for event in current_timestamp_events:
                if event.validator not in self.validators:
                    self.validators.append(event.validator)
                    self.validator_weights[event.validator] = event.weight
                elif event.validator not in self.confirmed_cheaters:
                    # If the validator reappears, reinstate its weight
                    self.validator_weights[event.validator] = event.weight

                self.detect_forks(event)
                self.set_highest_timestamps_observed(event)
                self.set_highest_events_observed(event)
                self.set_lowest_observing_events(event)
                self.set_roots(event)
                self.events.append(event)
                self.uuid_event_dict[event.uuid] = event

            self.time = timestamp

    def graph_results(self, output_filename):
        colors = ["orange", "yellow", "blue", "cyan", "purple"]
        green = mcolors.to_rgb("green")
        greens = [
            tuple(g * 0.7 for g in green),
            tuple(g * 0.8 for g in green),
            tuple(g * 0.9 for g in green),
            green,
        ]
        greens = [mcolors.to_hex(g) for g in greens]

        colors_rgb = [mcolors.to_rgb(color) for color in colors]

        darker_colors = []
        for color in colors_rgb:
            darker_color = tuple(c * 0.8 for c in color)
            darker_colors.append(mcolors.to_hex(darker_color))

        timestamp_dag = nx.DiGraph()

        # Add nodes and edges to graph
        for event in self.events:
            if event.validator in self.confirmed_cheaters:
                continue  # Skip nodes from confirmed cheaters
            validator = event.validator
            timestamp = event.timestamp
            sequence = event.sequence
            frame = event.frame
            weight = self.validator_weights[validator]
            root = event.root
            atropos = event.atropos
            timestamp_dag.add_node(
                (validator, timestamp),
                seq=sequence,
                frame=frame,
                weight=weight,
                root=root,
                atropos=atropos,
            )
            for parent_uuid in event.parents:
                parent = self.uuid_event_dict[parent_uuid]
                if parent.validator in self.confirmed_cheaters:
                    continue  # Skip edges that lead to confirmed cheaters
                parent_timestamp = parent.timestamp
                timestamp_dag.add_edge(
                    (validator, timestamp),
                    (parent.validator, parent_timestamp),
                )

        # Create color map
        color_map = {}
        for node in timestamp_dag:
            frame = timestamp_dag.nodes[node]["frame"]
            root = timestamp_dag.nodes[node]["root"]
            atropos = timestamp_dag.nodes[node]["atropos"]
            color_index = frame % len(colors)
            color_map[node] = (
                greens[frame % len(greens)]
                if atropos
                else (darker_colors[color_index] if root else colors[color_index])
            )

        pos = {}
        num_nodes = len(self.validator_weights)
        num_levels = max([event.timestamp for event in self.events])

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
            node: (
                node[0],
                node[1],
                timestamp_dag.nodes[node]["seq"],
                timestamp_dag.nodes[node]["weight"],
            )
            for node in timestamp_dag.nodes
        }

        nx.draw(
            timestamp_dag,
            pos,
            with_labels=True,
            labels={
                val: r"$\mathrm{{{}}}_{{{},{},{}}}$".format(
                    labels[val][0], labels[val][1], labels[val][2], labels[val][3]
                )
                for val in labels
            },
            font_family="serif",
            font_size=9,
            node_size=1300,
            node_color=[color_map[node] for node in timestamp_dag.nodes],
            font_weight="bold",
        )

        fig.savefig(output_filename, format="pdf", dpi=300, bbox_inches="tight")
        plt.close()


if __name__ == "__main__":
    event_list = parse_data("../inputs/cheaters/graph_81.txt")
    validators, validator_weights = filter_validators_and_weights(event_list)
    lachesis = Lachesis()
    lachesis.initialize_validators(validators, validator_weights)
    lachesis.process_events(event_list)
    lachesis.graph_results("result.pdf")
    print(lachesis.validator_weights)
    # print(lachesis.events)
    # print(lachesis.frame)
    # print(lachesis.root_set_events)
    # print(lachesis.graph_results("result.pdf"))
    # print(lachesis.validator_cheater_list)
    # print(lachesis.suspected_cheaters)
    # print(lachesis.confirmed_cheaters)
    # print(lachesis.highest_validator_timestamps)
    print(lachesis.frame)
    print(lachesis.block)
    print(lachesis.atropos_roots)

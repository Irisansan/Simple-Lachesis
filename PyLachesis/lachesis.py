from collections import deque
import os
import re
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from sortedcontainers import SortedSet

# this variable dictates how much "foresight" validators are allowed to have
# meaning, only validators within this field of view are known/seen and therefore
# initialized
global field_of_view
field_of_view = 5


def parse_data(file_path):
    event_list = []

    with open(file_path, "r") as file:
        for line in file:
            unique_id_match = re.search(r"unique_id:\s([a-z0-9-]*)", line)
            label_match = re.search(r"label:\s\(([\w\s]+),(\d+),(\d+),(\d+)\)", line)
            if not (unique_id_match and label_match):
                continue

            unique_id = unique_id_match.group(1)
            validator, timestamp, sequence, weight = label_match.groups()

            event = Event(
                validator, int(timestamp), int(sequence), int(weight), unique_id
            )
            event_list.append(event)

            child_unique_ids = re.findall(r"child_unique_id:\s([a-z0-9-]*)", line)
            for child_unique_id in child_unique_ids:
                event.add_parent(child_unique_id)

    return event_list


def filter_validators_and_weights(events):
    validators = []
    validator_weights = {}

    for event in events:
        if event.timestamp <= field_of_view and event.validator not in validators:
            validators.append(event.validator)
            validator_weights[event.validator] = event.weight

    return validators, validator_weights


class Event:
    def __init__(self, validator, timestamp, sequence, weight, unique_id):
        self.validator = validator
        self.timestamp = timestamp
        self.original_sequence = sequence
        self.sequence = sequence
        self.weight = weight
        self.uuid = unique_id
        self.frame = None
        self.root = False
        self.atropos = False
        self.highest_observed = {}
        self.lowest_observing = {}
        self.parents = []
        self.visited = {}

    def add_parent(self, parent_uuid):
        self.parents.append(parent_uuid)

    def __repr__(self):
        return f"\nEvent({self.validator}, {self.timestamp}, {self.sequence}, {self.weight}, {self.uuid}, {self.root})"

    def __eq__(self, other):
        if isinstance(other, Event):
            return (
                self.validator == other.validator
                and self.timestamp == other.timestamp
                and self.sequence == other.sequence
                and self.weight == other.weight
                and self.uuid == other.uuid
            )
        return False

    def __lt__(self, other):
        if isinstance(other, Event):
            return (
                self.validator,
                self.timestamp,
                self.sequence,
                self.weight,
                self.uuid,
            ) < (
                other.validator,
                other.timestamp,
                other.sequence,
                other.weight,
                other.uuid,
            )
        return NotImplemented

    def __hash__(self):
        return hash(
            (self.validator, self.timestamp, self.sequence, self.weight, self.uuid)
        )


class LachesisMultiInstance:
    def __init__(self, graph_results=False):
        self.file_path = None
        self.instances = {}
        self.graph_results = graph_results
        self.initial_validators = []
        self.initial_validator_weights = {}
        self.validators = []
        self.validator_weights = {}
        self.queued_validators = set()
        self.activation_queue = {}
        self.activated_time = {}
        self.seen_events = []
        self.time = 0

    def parse_and_initialize(self):
        event_list = parse_data(self.file_path)
        (
            self.initial_validators,
            self.initial_validator_weights,
        ) = filter_validators_and_weights(event_list)

        uuid_validator_map = {}
        for event in event_list:
            uuid_validator_map[event.uuid] = event.validator

        for validator in self.initial_validators:
            lachesis_instance = Lachesis(validator)
            lachesis_instance.initialize_validators(
                self.initial_validators, self.initial_validator_weights
            )
            self.instances[validator] = lachesis_instance
            self.validators.append(validator)
            self.validator_weights[validator] = self.initial_validator_weights[
                validator
            ]

        return event_list, uuid_validator_map

    def add_validator(self, event):
        self.validators.append(event.validator)
        self.validator_weights[event.validator] = event.weight
        self.activated_time[event.validator] = self.time
        lachesis_instance = Lachesis(event.validator)
        lachesis_instance.initialize_validators(
            self.initial_validators, self.initial_validator_weights
        )
        self.instances[event.validator] = lachesis_instance
        for v in self.activation_queue:
            lachesis_instance.activation_queue[v] = self.activation_queue[v]

    def process(self):
        (
            event_list,
            uuid_validator_map,
        ) = self.parse_and_initialize()

        timestamp_event_dict = {}

        for event in event_list:
            if event.timestamp not in timestamp_event_dict:
                timestamp_event_dict[event.timestamp] = []
            timestamp_event_dict[event.timestamp].append(event)

        max_timestamp = max(timestamp_event_dict.keys())
        min_timestamp = min(timestamp_event_dict.keys())

        for timestamp in range(min_timestamp, max_timestamp + 1):
            self.time = timestamp

            current_timestamp_events = timestamp_event_dict.get(timestamp, [])

            max_frame = max([self.instances[v].frame for v in self.validators])

            frames = []
            for v in self.validators:
                # one of the initial validators has not appeared, initialize as 1
                if (
                    v not in self.instances[v].validator_highest_frame
                    and v not in self.activation_queue
                ):
                    frames.append(1)
                # all other validators must be present (latent validators must first appear)
                # to account for their frames
                elif v in self.instances[v].validator_highest_frame:
                    frames.append(self.instances[v].validator_highest_frame[v])

            min_frame = min(frames) if len(frames) > 0 else 1

            timestamp_events = []

            for event in current_timestamp_events:
                if self.time > field_of_view:
                    if (
                        event.validator not in self.validators
                        and event.validator not in self.queued_validators
                    ):
                        self.queued_validators.add(event.validator)
                        (f, w) = max_frame + 1, event.weight
                        self.activation_queue[event.validator] = (f, w)
                        for validator in self.validators:
                            self.instances[validator].activation_queue[
                                event.validator
                            ] = (f, w)
                        continue

                    if (
                        event.validator not in self.instances
                        and min_frame >= self.activation_queue[event.validator][0]
                    ):
                        event.parents = [
                            p
                            for p in event.parents
                            if uuid_validator_map[p] != event.validator
                        ]
                        self.add_validator(event)
                        for seen_event in self.seen_events.copy():
                            cleared_event = Event(
                                seen_event.validator,
                                seen_event.timestamp,
                                seen_event.original_sequence,
                                seen_event.weight,
                                seen_event.uuid,
                            )
                            cleared_event.parents = seen_event.parents
                            self.instances[event.validator].process_queue[
                                seen_event.uuid
                            ] = cleared_event

                    if (
                        event.validator not in self.instances
                        and min_frame < self.activation_queue[event.validator][0]
                    ):
                        continue

                event.parents = [
                    p
                    for p in event.parents
                    if uuid_validator_map[p] in self.instances
                    and (
                        uuid_validator_map[p] not in self.activation_queue
                        or self.time > self.activated_time[uuid_validator_map[p]]
                    )
                ]

                cleared_event = Event(
                    event.validator,
                    event.timestamp,
                    event.original_sequence,
                    event.weight,
                    event.uuid,
                )
                cleared_event.parents = event.parents
                timestamp_events.append(cleared_event)

                instance = self.instances[event.validator]
                instance.defer_event(event, self.instances, uuid_validator_map)

            for instance in self.instances.values():
                instance.process_request_queue(self.instances)

            for instance in self.instances.values():
                instance.process_deferred_events()

            self.seen_events.extend(timestamp_events)

    def run_lachesis_multiinstance(
        self, input_filename, output_folder, graph_results=False
    ):
        self.file_path = input_filename
        self.graph_results = graph_results
        self.process()

        reference = Lachesis()
        reference.run_lachesis(
            input_filename, "./result.pdf", graph_results=graph_results
        )

        if self.graph_results:
            for validator, instance in self.instances.items():
                output_filename = os.path.join(
                    output_folder, f"validator_{validator}_result.pdf"
                )
                instance.graph_results(output_filename)

        for instance in self.instances.values():
            # print(self.activation_queue)
            # print(instance.validator, instance.validators)
            assert (
                instance.frame <= reference.frame
            ), f"Frame is greater in instance {instance.validator}"
            assert (
                instance.block <= reference.block
            ), f"Block is greater in instance {instance.validator}"
            assert (
                instance.time <= reference.time
            ), f"Time is greater in instance {instance.validator}"
            assert (
                instance.frame_to_decide <= reference.frame_to_decide
            ), f"Frame to decide is greater in instance {instance.validator}"
            for key in instance.quorum_cache.keys():
                assert (
                    key in reference.quorum_cache.keys()
                ), f"Key {key} in quorum_cache not found in reference"
                assert (
                    instance.quorum_cache[key] == reference.quorum_cache[key]
                ), f"Quorum cache value for frame {key} in instance {instance.validator} does not match reference"
            assert set(instance.root_set_validators).issubset(
                set(reference.root_set_validators)
            ), f"Root set validators in instance {instance.validator} not a subset of reference"
            assert set(instance.events).issubset(
                set(reference.events)
            ), f"Events in instance {instance.validator} not a subset of reference"
            for f in reference.root_set_events:
                assert SortedSet(instance.root_set_events.get(f, [])) <= SortedSet(
                    reference.root_set_events[f]
                ), f"Root set events for frame {f} in instance {instance.validator} is not a subset of reference"
            assert set(instance.validator_cheater_list.keys()).issubset(
                set(reference.validator_cheater_list.keys())
            ), f"Validator cheater list in instance {instance.validator} not a subset of reference"
            assert set(
                [v for k, v in instance.atropos_roots.items() if k < reference.block]
            ).issubset(
                set(reference.atropos_roots.values())
            ), f"Atropos roots in instance {instance.validator} not a subset of reference up to block {reference.block}"


class Lachesis:
    def __init__(self, validator=None):
        self.validator = validator
        self.validators = []
        self.validator_weights = {}
        self.time = 1
        self.events = []
        self.frame = 1
        self.epoch = 1
        self.root_set_validators = {}
        self.root_set_events = {}
        self.observed_sequences = {}
        self.validator_cheater_list = {}
        self.validator_cheater_times = {}
        self.validator_confirmed_cheaters = {}
        self.validator_visited_events = {}
        self.validator_highest_frame = {}
        self.activation_queue = {}
        self.validator_delay = {}
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
        self.request_queue = deque()
        self.process_queue = {}
        self.minimum_frame = 1
        self.frame_times = []

    def initialize_validators(self, validators=None, validator_weights=None):
        self.validators = [] if validators is None else validators.copy()
        self.validator_weights = (
            {} if validator_weights is None else validator_weights.copy()
        )

    def defer_event(self, event, instances, uuid_validator_map):
        cleared_event = Event(
            event.validator,
            event.timestamp,
            event.original_sequence,
            event.weight,
            event.uuid,
        )
        cleared_event.parents = event.parents
        self.process_queue[event.uuid] = cleared_event
        for parent_uuid in event.parents:
            if (
                parent_uuid not in self.process_queue
                and parent_uuid not in self.uuid_event_dict
            ):
                parent_validator = uuid_validator_map.get(parent_uuid)
                if (
                    parent_validator is not None
                    and parent_validator in instances
                    and parent_validator is not event.validator
                ):
                    parent_creator_instance = instances[parent_validator]
                    parent_creator_instance.request_queue.append(
                        (self.validator, parent_uuid)
                    )

    def process_request_queue(self, instances):
        while self.request_queue:
            requestor_id, requested_uuid = self.request_queue.popleft()
            requestor_instance = instances[requestor_id]
            requested_event = self.uuid_event_dict[requested_uuid]
            cleared_requested_event = Event(
                requested_event.validator,
                requested_event.timestamp,
                requested_event.original_sequence,
                requested_event.weight,
                requested_event.uuid,
            )
            cleared_requested_event.parents = requested_event.parents
            requestor_instance.process_queue[requested_uuid] = cleared_requested_event

            for event_uuid, event in self.uuid_event_dict.items():
                if (
                    (
                        event.timestamp < requested_event.timestamp
                        or (
                            event.timestamp == requested_event.timestamp
                            and self.validator == requested_event.validator
                        )
                    )
                    and event_uuid not in requestor_instance.uuid_event_dict
                    and event_uuid not in requestor_instance.process_queue
                ):
                    cleared_event = Event(
                        event.validator,
                        event.timestamp,
                        event.original_sequence,
                        event.weight,
                        event.uuid,
                    )
                    cleared_event.parents = event.parents

                    requestor_instance.process_queue[event_uuid] = cleared_event

    def process_deferred_events(self):
        if self.process_queue:
            self.process_events(list(self.process_queue.values()))
            self.process_queue.clear()

    def quorum(self, frame):
        for v in self.activation_queue:
            (f, w) = self.activation_queue[v]
            if frame >= f and v not in self.validators:
                self.validators.append(v)
                self.validator_weights[v] = w

        if frame in self.quorum_cache:
            return self.quorum_cache[frame]

        weights_total = sum(
            self.validator_weights[v]
            for v in self.validators
            if v not in self.activation_queue or frame >= self.activation_queue[v][0]
        )

        self.quorum_cache[frame] = 2 * weights_total // 3 + 1
        return self.quorum_cache[frame]

    def is_root(self, event):
        if event.sequence == 1:
            return True

        event.frame = max(
            [
                e.frame
                for e in self.events
                if e.validator == event.validator and e.sequence < event.sequence
            ]
        )

        if event.validator not in self.validator_highest_frame:
            self.validator_highest_frame[event.validator] = event.frame
        elif event.frame > self.validator_highest_frame[event.validator]:
            self.validator_highest_frame[event.validator] = event.frame

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
                event.frame = 1
                if event.validator in self.activation_queue:
                    event.frame = self.activation_queue[event.validator][0]
            else:
                event.frame += 1
            if self.frame < event.frame:
                self.frame = event.frame
            if event.frame in self.root_set_events:
                self.root_set_events[event.frame].append(event)
                self.root_set_validators[event.frame].append(event.validator)
            else:
                self.root_set_events[event.frame] = [event]
                self.root_set_validators[event.frame] = [event.validator]
                self.frame_times.append(self.time)
                self.quorum(event.frame)

        if event.validator not in self.validator_highest_frame:
            self.validator_highest_frame[event.validator] = event.frame
        elif event.frame > self.validator_highest_frame[event.validator]:
            self.validator_highest_frame[event.validator] = event.frame

    def atropos_voting(self, new_root):
        candidates = self.root_set_events[self.frame_to_decide]

        for candidate in candidates:
            if candidate.uuid in self.decided_roots:
                continue

            if self.frame_to_decide not in self.election_votes:
                self.election_votes[self.frame_to_decide] = {}

            if (new_root.uuid, candidate.uuid) not in self.election_votes[
                self.frame_to_decide
            ]:
                vote = None

                if new_root.frame == self.frame_to_decide + 1:
                    vote = {
                        "decided": False,
                        "yes": self.forkless_cause(new_root, candidate),
                    }
                elif new_root.frame >= self.frame_to_decide + 2:
                    yes_votes = 0
                    no_votes = 0

                    for prev_root in self.root_set_events[new_root.frame - 1]:
                        prev_vote = self.election_votes[self.frame_to_decide].get(
                            (prev_root.uuid, candidate.uuid), {"yes": False}
                        )
                        if prev_vote["yes"]:
                            yes_votes += self.validator_weights[prev_root.validator]
                        else:
                            no_votes += self.validator_weights[prev_root.validator]

                    vote = {
                        "decided": yes_votes >= self.quorum(self.frame_to_decide)
                        or no_votes >= self.quorum(self.frame_to_decide),
                        "yes": yes_votes >= no_votes,
                    }

                if vote is not None:
                    self.election_votes[self.frame_to_decide][
                        (new_root.uuid, candidate.uuid)
                    ] = vote

                    if vote["decided"]:
                        self.decided_roots[candidate.uuid] = vote

        for candidate in sorted(
            candidates, key=lambda event: (-event.weight, event.uuid)
        ):
            if (
                candidate.uuid in self.decided_roots
                and self.decided_roots[candidate.uuid]["yes"]
            ):
                self.atropos_roots[self.frame_to_decide] = candidate.uuid
                candidate.atropos = True
                self.frame_to_decide += 1
                self.block += 1
                return

    def process_known_roots(self):
        for frame in range(self.frame_to_decide + 1, self.frame):
            frame_roots = self.root_set_events[frame]
            for root in frame_roots:
                self.atropos_voting(root)

    def forkless_cause(self, event_a, event_b):
        if (
            event_b.validator
            in self.validator_cheater_list.get(event_a.validator, set())
            and self.validator_cheater_times[event_a.validator][event_b.validator]
            <= event_a.timestamp
        ):
            return False

        a = {
            validator: observed["sequence"]
            for validator, observed in event_a.highest_observed.items()
        }
        b = event_b.lowest_observing

        yes = 0
        for validator, sequence in a.items():
            if validator in b and b[validator]["sequence"] <= sequence:
                uuid_a = event_a.highest_observed[validator]["uuid"]
                uuid_b = event_b.lowest_observing[validator]["uuid"]

                is_branch = uuid_a in self.validator_visited_events.get(
                    event_a.validator, set()
                ) and uuid_b in self.validator_visited_events.get(
                    event_a.validator, set()
                )

                no_forks = (
                    event_a.validator not in self.validator_cheater_list
                    or validator not in self.validator_cheater_list[event_a.validator]
                    or (
                        is_branch
                        and self.uuid_event_dict[uuid_a].timestamp
                        < self.validator_cheater_times[event_a.validator][validator]
                        and self.uuid_event_dict[uuid_b].timestamp
                        < self.validator_cheater_times[event_a.validator][validator]
                    )
                )

                if is_branch and no_forks:
                    yes += self.validator_weights[validator]

        return yes >= self.quorum(event_b.frame)

    def detect_forks(self, event):
        if event.validator not in self.validator_cheater_list:
            self.validator_cheater_list[event.validator] = set()

        parents = deque(event.parents)

        while parents:
            parent_id = parents.popleft()
            parent = self.uuid_event_dict[parent_id]

            if event.validator not in parent.visited:
                parent.visited[event.validator] = {
                    "uuid": event.uuid,
                    "sequence": event.sequence,
                }

                if event.validator not in self.validator_visited_events:
                    self.validator_visited_events[event.validator] = set(
                        str(event.uuid)
                    )
                self.validator_visited_events[event.validator].add((str(parent.uuid)))

                if event.validator not in self.observed_sequences:
                    self.observed_sequences[event.validator] = {}
                if parent.validator not in self.observed_sequences[event.validator]:
                    self.observed_sequences[event.validator][parent.validator] = set()

                if (
                    parent.sequence
                    in self.observed_sequences[event.validator][parent.validator]
                ):
                    self.validator_cheater_list[event.validator].add(parent.validator)
                    if event.validator not in self.validator_cheater_times:
                        self.validator_cheater_times[event.validator] = {}
                    if (
                        parent.validator
                        not in self.validator_cheater_times[event.validator]
                    ):
                        self.validator_cheater_times[event.validator][
                            parent.validator
                        ] = event.timestamp
                    self.suspected_cheaters.add(parent.validator)
                else:
                    self.observed_sequences[event.validator][parent.validator].add(
                        parent.sequence
                    )
                parents.extend(parent.parents)

    def set_highest_events_observed(self, event):
        for parent_id in event.parents:
            parent = self.uuid_event_dict[parent_id]

            if (
                parent.validator not in event.highest_observed
                or parent.sequence
                > event.highest_observed[parent.validator]["sequence"]
                or (
                    parent.validator in event.highest_observed
                    and parent.sequence
                    == event.highest_observed[parent.validator]["sequence"]
                    and parent.uuid < event.highest_observed[parent.validator]["uuid"]
                )
            ):
                event.highest_observed[parent.validator] = {
                    "uuid": parent.uuid,
                    "sequence": parent.sequence,
                }

            for validator, observed in parent.highest_observed.items():
                if (
                    validator not in event.highest_observed
                    or observed["sequence"]
                    > event.highest_observed[validator]["sequence"]
                    or (
                        validator in event.highest_observed
                        and observed["sequence"]
                        == event.highest_observed[validator]["sequence"]
                        and parent.uuid < event.highest_observed[validator]["uuid"]
                    )
                ):
                    event.highest_observed[validator] = observed.copy()

    def set_lowest_observing_events(self, event):
        parents = deque(event.parents)

        while parents:
            parent_id = parents.popleft()
            parent = self.uuid_event_dict[parent_id]

            if event.validator not in parent.lowest_observing or (
                parent.lowest_observing[event.validator]["sequence"] > event.sequence
                and self.uuid_event_dict[
                    parent.lowest_observing[event.validator]["uuid"]
                ].timestamp
                == event.timestamp
                or (
                    parent.lowest_observing[event.validator]["sequence"]
                    == event.sequence
                    and event.uuid < parent.lowest_observing[event.validator]["uuid"]
                    and self.uuid_event_dict[
                        parent.lowest_observing[event.validator]["uuid"]
                    ].timestamp
                    == event.timestamp
                )
            ):
                parent.lowest_observing[event.validator] = {
                    "uuid": event.uuid,
                    "sequence": event.sequence,
                }

                if (
                    event.validator in self.validator_cheater_list
                    and parent.validator in self.validator_cheater_list[event.validator]
                    and self.time
                    >= self.validator_cheater_times[event.validator][parent.validator]
                ):
                    continue

                parents.extend(parent.parents)

    def process_events(self, events):
        timestamp_event_dict = {}
        for event in events:
            if event.timestamp not in timestamp_event_dict:
                timestamp_event_dict[event.timestamp] = []
            timestamp_event_dict[event.timestamp].append(event)

        max_timestamp = max(timestamp_event_dict.keys())
        min_timestamp = min(timestamp_event_dict.keys())

        for timestamp in range(min_timestamp, max_timestamp + 1):
            self.time = timestamp
            frames = []
            for v in self.validators:
                # one of the initial validators has not appeared, initialize as 1
                if (
                    v not in self.validator_highest_frame
                    and v not in self.activation_queue
                ):
                    frames.append(1)
                # all other validators must be present (latent validators must first appear)
                # to account for their frames
                elif v in self.validator_highest_frame:
                    frames.append(self.validator_highest_frame[v])

            min_frame = min(frames) if len(frames) > 0 else 1

            if min_frame >= self.minimum_frame:
                self.minimum_frame = min_frame

            current_timestamp_events = timestamp_event_dict.get(timestamp, [])

            current_timestamp_events.sort(key=lambda e: (-e.sequence, e.uuid))

            for event in current_timestamp_events:
                if (
                    event.validator not in self.validators
                    and event.timestamp <= field_of_view
                ):
                    self.validators.append(event.validator)
                    self.validator_weights[event.validator] = event.weight

                if (
                    event.validator not in self.validators
                    and self.time > field_of_view
                    and event.validator not in self.activation_queue
                ):
                    self.activation_queue[event.validator] = (
                        self.frame + 1,
                        event.weight,
                    )
                    continue

            for event in current_timestamp_events:
                event.parents = [p for p in event.parents if p in self.uuid_event_dict]

                if (
                    event.validator not in self.validator_highest_frame
                    and event.validator in self.activation_queue
                    and self.minimum_frame < self.activation_queue[event.validator][0]
                ):
                    continue

                if (
                    event.validator in self.activation_queue
                    and self.minimum_frame >= self.activation_queue[event.validator][0]
                ):
                    event.sequence = 1
                    for p in event.parents:
                        if (
                            self.uuid_event_dict[p].validator == event.validator
                            and self.uuid_event_dict[p].original_sequence + 1
                            == event.original_sequence
                        ):
                            event.sequence = self.uuid_event_dict[p].sequence + 1

                self.detect_forks(event)
                self.set_highest_events_observed(event)
                self.set_lowest_observing_events(event)
                self.set_roots(event)
                self.events.append(event)
                self.uuid_event_dict[event.uuid] = event
                self.process_known_roots()

    def graph_results(self, output_filename):
        colors = ["orange", "yellow", "cyan", "blue", "purple"]
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

        for event in self.events:
            if event.validator in self.suspected_cheaters:
                continue
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
                if parent.validator in self.suspected_cheaters:
                    continue
                parent_timestamp = parent.timestamp
                timestamp_dag.add_edge(
                    (validator, timestamp),
                    (parent.validator, parent_timestamp),
                )

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

    def run_lachesis(self, input_filename, output_filename, graph_results=False):
        event_list = parse_data(input_filename)
        validators, validator_weights = filter_validators_and_weights(event_list)

        self.initialize_validators(validators, validator_weights)
        self.process_events(event_list)

        if graph_results:
            self.graph_results(output_filename)


if __name__ == "__main__":
    lachesis_single_instance = Lachesis()
    lachesis_single_instance.run_lachesis(
        "../inputs/graphs/graph_167.txt",
        "./result.pdf",
        True,
    )
    lachesis_multi_instance = LachesisMultiInstance()
    lachesis_multi_instance.run_lachesis_multiinstance(
        "../inputs/graphs/graph_167.txt", "./", False
    )

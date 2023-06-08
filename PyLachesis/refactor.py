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
        self.highest_observed = {}
        self.lowest_observing = {}
        self.visited = {}
        self.parents = []

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
        self.quorum_values = None
        self.uuid_event_dict = {}

    def initialize_validators(self, validators, validator_weights):
        self.validators = validators
        self.validator_weights = validator_weights

    def quorum(self, frame):
        return (
            2
            * sum(
                [
                    self.validator_weights[root.validator]
                    for root in self.root_set_events[frame]
                ]
            )
            // 3
            + 1
        )

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
            if event.sequence == 1:
                event.frame = 1
            else:
                event.frame += 1
            if self.frame < event.frame:
                self.frame = event.frame
            if event.frame in self.root_set_events:
                self.root_set_events[event.frame].append(event)
            else:
                self.root_set_events[event.frame] = [event]

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
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        # Add events to Lachesis
        for event in sorted_events:
            self.detect_forks(event)
            self.set_highest_events_observed(event)
            self.set_lowest_observing_events(event)
            self.set_roots(event)
            self.events.append(event)
            self.uuid_event_dict[event.uuid] = event


if __name__ == "__main__":
    event_list = parse_data("../inputs/cheaters/graph_3.txt")
    validators, validator_weights = filter_validators_and_weights(event_list)
    lachesis = Lachesis()
    lachesis.initialize_validators(validators, validator_weights)
    lachesis.process_events(event_list)
    print(lachesis.validator_weights)
    print(lachesis.validator_cheater_list)
    print(lachesis.frame)
    print(lachesis.root_set_events)

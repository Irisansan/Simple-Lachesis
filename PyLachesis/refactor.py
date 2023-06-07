from collections import deque
import re


def parse_data(file_path):
    uuid_event_dict = {}
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
            uuid_event_dict[unique_id] = event
            event_list.append(event)

            # Add parents if they exist
            child_unique_ids = re.findall(r"child_unique_id:\s([a-z0-9-]*)", line)
            for child_unique_id in child_unique_ids:
                if child_unique_id in uuid_event_dict:
                    event.add_parent(child_unique_id)

    return uuid_event_dict, event_list


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
        self.frame = None
        self.epoch = None
        self.root_set_validators = []
        self.root_set_events = {}
        self.frame_to_decide = None
        self.validator_cheater_list = {}
        self.decided_roots = []
        self.atropos_roots = []
        self.quorum = None
        self.uuid_event_dict = {}

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

            # If the validator of the event is not in the parent vector, add it
            if event.validator not in parent.lowest_observing:
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
            self.set_highest_events_observed(event)
            self.set_lowest_observing_events(event)
            self.events.append(event)
            self.uuid_event_dict[event.uuid] = event


if __name__ == "__main__":
    uuid_event_dict, event_list = parse_data("../inputs/cheaters/graph_7.txt")
    lachesis = Lachesis()
    lachesis.process_events(event_list)
    print(lachesis.uuid_event_dict)
    print(lachesis.events)
    print(lachesis.validator_cheater_list)

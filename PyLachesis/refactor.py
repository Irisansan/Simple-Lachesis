import re
import uuid


def parse_data(file_path):
    event_dict = {}
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
            event_dict[unique_id] = event

            # Add parents if they exist
            child_unique_ids = re.findall(r"child_unique_id:\s([a-z0-9-]*)", line)
            for child_unique_id in child_unique_ids:
                if child_unique_id in event_dict:
                    event.add_parent(child_unique_id)

    return event_dict


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
        return f"Event({self.validator}, {self.timestamp}, {self.sequence}, {self.weight}, {self.uuid}, {self.parents})"


if __name__ == "__main__":
    event_dict = parse_data("../inputs/graphs/graph_1.txt")
    print(event_dict)

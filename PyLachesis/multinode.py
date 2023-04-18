from lachesis import Event
from lachesis import Lachesis
from input_to_dag import convert_input_to_DAG


def process_input(graph_file, graph_results=False, output_filename=None):
    graph = convert_input_to_DAG(graph_file)
    validator_set = {node[0] for node in graph.nodes}
    validator_weights = {node[0][0]: 1 for node in graph.nodes(data=True)}
    validator_instances = {
        validator: Lachesis(validator) for validator in validator_set
    }

    for instance in validator_instances.values():
        instance.validator_weights = validator_weights
        instance.init_validator_instances(validator_instances)

    nodes = sorted(graph.nodes(data=True), key=lambda node: node[1]["timestamp"])
    max_timestamp = max([node[1]["timestamp"] for node in nodes])

    for current_time in range(max_timestamp + 1):
        nodes_to_process = [
            node for node in nodes if node[1]["timestamp"] == current_time
        ]

        for node in nodes_to_process:
            parent_ids = [
                (parent[0], graph.nodes[parent]["predecessors"])
                for parent in graph.successors(node[0])
            ]
            parent_events = []
            for parent_id in parent_ids:
                parent_validator = parent_id[0]
                parent_event, _ = validator_instances[parent_validator].request_event(
                    parent_id
                )
                if parent_event is not None:
                    parent_events.append(parent_event.id)  # Use parent event IDs

            validator = node[0][0]
            seq = node[1]["predecessors"]

            event = Event(
                id=(validator, seq),
                seq=seq,
                creator=node[0][0],
                parents=parent_events,  # Pass parent event IDs
            )

            validator_instances[validator].event_timestamps[event.id] = current_time
            validator_instances[validator].receive_event(event, current_time)
            validator_instances[validator].process_events()
            validator_instances[validator].time = current_time

        # Call process_events for each validator instance after receiving the event
        for instance in validator_instances.values():
            instance.time = current_time
            instance.process_events()

    if graph_results and output_filename:
        first_validator_instance = next(iter(validator_instances.values()))
        first_validator_instance.graph_results(output_filename)


if __name__ == "__main__":
    process_input("../inputs/graphs/graph_1.txt", True, "multinoderesults.pdf")

import networkx as nx


def convert_input_to_DAG(input_file):
    G = nx.DiGraph()

    with open(input_file, "r") as f:
        for line in f:
            line = line.strip()

            parts = line.split(";")

            node_info = parts[0].strip()[6:-1]
            node_id, timestamp, predecessors = node_info.split(",")
            timestamp, predecessors = int(timestamp), int(predecessors)

            G.add_node(
                (node_id[1:], timestamp),
                timestamp=timestamp,
                predecessors=predecessors,
                weight=1,
                lowest_events_which_observe_event={},
                highest_events_observed_by_event={},
            )

            for child_info in parts[1:]:
                child_info = child_info.strip()[7:-1]
                child_info_parts = child_info.split(",")
                if len(child_info_parts) < 2:
                    continue
                child_id, child_timestamp = child_info_parts[:2]
                child_timestamp = int(child_timestamp)

                G.add_edge((node_id[1:], timestamp), (child_id[1:], child_timestamp))

    """
    print("Nodes in the graph:")
    for node in G.nodes(data=True):
        print(node)

    print("Edges in the graph:")
    for edge in G.edges():
        print(edge)
    """

    return G


if __name__ == "__main__":
    pass
    convert_input_to_DAG("graph_10.txt")

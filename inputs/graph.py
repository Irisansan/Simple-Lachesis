import uuid
import networkx as nx
import matplotlib.pyplot as plt
import random
import matplotlib
import math

matplotlib.use("Agg")


def logistic(L, k, x0, x):
    return L / (1 + math.exp(-k * (x - x0)))


def random_weight(x):
    return int(logistic(40, 0.2, 25, x) * random.random()) + 1


def createGraph(
    cheater_probability,
    num_levels,
    num_nodes,
    node_present_probability,
    observing_probability,
    neighbor_probability,
    annotate=False,
    show_graph=False,
    save_plot=False,
    graph_filename="graph.png",
    txt_filename_format_one="txt.txt",
    txt_filename_format_two="txt2.txt",
    neighbor_filename="neighbors.txt",
):
    # Initialize the graph
    G = nx.DiGraph()

    weights = [random_weight(num_nodes) for j in range(num_nodes)]

    # Create the neighbors dictionary
    neighbors = {}
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            if random.random() < neighbor_probability:
                if i not in neighbors:
                    neighbors[i] = set()
                if j not in neighbors:
                    neighbors[j] = set()
                neighbors[i].add(j)
                neighbors[j].add(i)

    # Ensure each node has at least one neighbor
    unconnected_nodes = set(range(num_nodes))
    while unconnected_nodes:
        node1 = random.choice(list(unconnected_nodes))
        unconnected_nodes.remove(node1)
        if node1 not in neighbors:
            neighbors[node1] = set()

        if not neighbors[node1]:
            available_nodes = unconnected_nodes.difference({node1})
            if not available_nodes:
                available_nodes = (
                    set(range(num_nodes))
                    .difference({node1})
                    .difference(neighbors[node1])
                )
            node2 = random.choice(list(available_nodes))

            if node2 not in neighbors:
                neighbors[node2] = set()

            neighbors[node1].add(node2)
            neighbors[node2].add(node1)
            unconnected_nodes.discard(node2)

    # Save neighbors dictionary to a file
    with open(neighbor_filename, "w") as f:
        for key, values in neighbors.items():
            f.write(
                f"{chr(key + 65)}: {', '.join(chr(value + 65) for value in values)}\n"
            )

    # Add nodes and assign colors
    colors = [
        "red",
        "orange",
        "yellow",
        "green",
        "blue",
        "cyan",
        "pink",
        "purple",
        "gray",
        "olive",
        "brown",
    ]
    color_map = {}
    parent_count = {}
    cheater_nodes = {}

    start_times = [
        random.randint(0, num_levels) if random.random() < 0.1 else 0
        for _ in range(num_nodes)
    ]
    stop_times = [
        random.randint(0, num_levels) if random.random() < 0.1 else num_levels - 1
        for _ in range(num_nodes)
    ]

    for j in range(num_nodes):
        if start_times[j] > stop_times[j]:
            start_times[j], stop_times[j] = stop_times[j], start_times[j]

    for i in range(num_levels):
        for j in range(num_nodes):
            if i < start_times[j] or i > stop_times[j]:
                continue

            if (
                i == stop_times[j] and i <= num_levels - 1
            ) or random.random() < node_present_probability:
                node = (i, j)
                G.add_node(node)
                if i == 0:
                    color_map[node] = colors[j % len(colors)]
                    parent_count[node] = 0
                else:
                    parent = (i - 1, j)
                    self_ref = False
                    while not self_ref and parent[0] >= 0:
                        if parent in G.nodes:
                            if parent in color_map:
                                color_map[node] = color_map[parent]
                                parent_count[node] = parent_count[parent] + 1
                            else:
                                color_map[node] = colors[j % len(colors)]
                                parent_count[node] = 0
                            G.add_edge(node, parent)
                            self_ref = True
                        parent = (parent[0] - 1, parent[1])
                if node not in color_map:
                    color_map[node] = colors[j % len(colors)]
                    parent_count[node] = 0
                if not any(n[1] == j and n[0] < i for n in G.nodes):
                    if random.random() < cheater_probability:
                        for k in random.sample(range(num_nodes), num_nodes):
                            if k != j and (i - 1, k) in G.nodes:
                                cheater_nodes[node] = (i - 1, k)
                                stop_times[j] = stop_times[k]
                                target = (i - 1, k)
                                G.add_edge(node, target)
                                break

    # Add edges
    for i in range(num_levels):
        for j in range(num_nodes):
            node = (i, j)
            if node in G.nodes and node not in cheater_nodes.keys():
                parent = (i - 1, j)
                self_ref = False
                while not self_ref and parent[0] >= 0:
                    if parent in G.nodes and parent[1] in neighbors.get(node[1], set()):
                        G.add_edge(node, parent)
                        self_ref = True
                    parent = (parent[0] - 1, parent[1])
                for k in range(num_nodes):
                    if random.random() < observing_probability:
                        target = (i - 1, k)
                        if target in G.nodes and target[1] in neighbors.get(
                            node[1], set()
                        ):
                            G.add_edge(node, target)

    labels = {
        (i, j): (
            chr(j + 65),
            i + 1,
            parent_count[(i, j)] + 1,
            weights[j],
            True if i == stop_times[j] else False,
        )
        for i in range(num_levels)
        for j in range(num_nodes)
        if (i, j) in G.nodes
    }

    # Cheaters inherit the color and letter of the deepest cheater
    for node in cheater_nodes.keys():
        # print("node:", node, ", parent", cheater_nodes[node])
        i, j = node[0], node[1]

        cheating_parents = 0
        deepest_cheater = cheater_nodes[node]
        # Iterate back along the row to see if a deeper node is a cheater
        for _i in range(deepest_cheater[0], -1, -1):
            if (_i, deepest_cheater[1]) in G.nodes:
                cheating_parents += 1
                deepest_cheater = (_i, deepest_cheater[1])

        while deepest_cheater in cheater_nodes.keys():
            deepest_cheater = cheater_nodes[deepest_cheater]
            for _i in range(deepest_cheater[0], -1, -1):
                if (_i, deepest_cheater[1]) in G.nodes:
                    cheating_parents += 1
                    deepest_cheater = (_i, deepest_cheater[1])

        for i in range(num_levels):
            if (i, j) in G.nodes:
                labels[(i, j)] = (
                    chr(deepest_cheater[1] + 65),
                    i + 1,
                    cheating_parents + 1,
                    weights[deepest_cheater[1]],  # inherit weight from deepest cheater
                    True
                    if i == stop_times[deepest_cheater[1]]
                    else False,  # the missing part
                )
                cheating_parents += 1
                color_map[(i, j)] = color_map[(deepest_cheater)]

    # Plot the figure
    figsize = [20, 10]
    # Scale the figure size proportionally to the number of levels and nodes
    if num_levels >= 15:
        figsize[0] = figsize[0] * num_levels / 20
    if num_nodes >= 10:
        figsize[0] = figsize[0] * num_nodes / 4
        figsize[1] = figsize[1] * num_nodes / 10
    fig = plt.figure(figsize=(figsize[0], figsize[1]))
    pos = {(i, j): (i, j) for i in range(num_levels) for j in range(num_nodes)}
    nx.draw(
        G,
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
        node_color=[color_map.get(node, color_map[node]) for node in G.nodes()],
        node_size=1300,
        font_weight="bold",
    )

    if annotate:
        plt.text(
            0.007,
            0.98,
            "node_present_probability: {}".format(node_present_probability),
            fontsize=8,
            fontname="monospace",
            transform=fig.transFigure,
        )
        plt.text(
            0.007,
            0.96,
            "observing_probability: {}".format(observing_probability),
            fontsize=8,
            fontname="monospace",
            transform=fig.transFigure,
        )
        plt.text(
            0.007,
            0.94,
            "num_nodes: {}".format(num_nodes),
            fontsize=8,
            fontname="monospace",
            transform=fig.transFigure,
        )
        plt.text(
            0.007,
            0.92,
            "num_levels: {}".format(num_levels),
            fontsize=8,
            fontname="monospace",
            transform=fig.transFigure,
        )
        plt.text(
            0.007,
            0.90,
            "cheat_prob: {}".format(cheater_probability),
            fontsize=8,
            fontname="monospace",
            transform=fig.transFigure,
        )
    # print(cheater_nodes)

    # Save graph as text data in format one
    node_uuids = {}

    with open(txt_filename_format_one, "w") as f:
        for node in G:
            if node not in node_uuids:
                node_uuids[node] = uuid.uuid4()
            node_uuid = node_uuids[node]
            f.write(
                "unique_id: "
                + str(node_uuid)
                + " label: ("
                + str(labels[node][0])
                + ","
                + str(labels[node][1])
                + ","
                + str(labels[node][2])
                + ","
                + str(labels[node][3])
                + ","
                + str(labels[node][4])
                + ")"
            )
            f.write(";")
            for child in G[node]:
                if child not in node_uuids:
                    node_uuids[child] = uuid.uuid4()
                child_uuid = node_uuids[child]
                f.write(
                    " child_unique_id: "
                    + str(child_uuid)
                    + " child_label: ("
                    + str(labels[child][0])
                    + ","
                    + str(labels[child][1])
                    + ","
                    + str(labels[child][2])
                    + ");"
                )
            f.write("\n")

    # # Save graph as text data in format two
    # with open(txt_filename_format_two, "w") as f:
    #     for node in G:
    #         validator = "Event" + labels[node][0]
    #         epoch = "1"  # affixed to 1 for now
    #         seq = str(labels[node][2])
    #         event = validator + seq
    #         creator = (
    #             chr(cheater_nodes[node][1] + 65)
    #             if node in cheater_nodes.keys()
    #             else chr(node[1] + 65)
    #         )
    #         node_information = ";".join([event, epoch, seq, creator])
    #         children_information = ",".join(
    #             [
    #                 "Event" + labels[child][0] + str(labels[child][2])
    #                 for child in G[node]
    #             ]
    #         )

    #         f.write(node_information + ";" + children_information)
    #         f.write("\n")

    # Save plot as a PDF
    if save_plot:
        manager = plt.get_current_fig_manager()
        manager.full_screen_toggle()
        fig.savefig(graph_filename, format="pdf", dpi=300, bbox_inches="tight")
    if show_graph:
        plt.show()
    plt.close()


def generate_graphs(
    annotate_graph,
    num_graphs,
    cheater_input,
    level_input,
    node_input,
    present_prob_input,
    observe_prob_input,
    neighbor_prob_input,
    base_dir,
    starting_index,
):
    annotate = True if annotate_graph.lower() == "y" else False
    num_graphs = int(num_graphs) if num_graphs else 50
    cheater_input = (
        float(cheater_input)
        if (cheater_input is not None and cheater_input.strip() != "")
        else 0.2
    )
    level_input = (
        int(level_input)
        if level_input and str(level_input).lower() not in ["r", "random"]
        else None
    )
    node_input = (
        int(node_input)
        if node_input and str(node_input).lower() not in ["r", "random"]
        else None
    )
    present_prob_input = (
        float(present_prob_input)
        if present_prob_input and str(present_prob_input).lower() not in ["r", "random"]
        else None
    )
    observe_prob_input = (
        float(observe_prob_input)
        if observe_prob_input and str(observe_prob_input).lower() not in ["r", "random"]
        else None
    )
    neighbor_prob_input = (
        float(neighbor_prob_input)
        if neighbor_prob_input
        and str(neighbor_prob_input).lower() not in ["r", "random"]
        else None
    )

    for i in range(num_graphs):
        num_levels = random.randint(5, 100) if level_input is None else level_input
        num_nodes = random.randint(3, 25) if node_input is None else node_input
        node_present_probability = (
            random.uniform(0.5, 0.7)
            if present_prob_input is None
            else present_prob_input
        )
        observing_probability = (
            random.uniform(0.2, 0.4)
            if observe_prob_input is None
            else observe_prob_input
        )
        neighbor_probability = (
            random.uniform(0.1, 0.9)
            if neighbor_prob_input is None
            else neighbor_prob_input
        )

        graph_index = str(int(starting_index) + (i))

        graph_filename = f"{base_dir}/graph_{graph_index}.pdf"
        txt_filename_format_one = f"{base_dir}/graph_{graph_index}.txt"
        txt_filename_format_two = f"{base_dir}/events_{graph_index}.txt"
        neighbor_filename = f"{base_dir}/neighbors_{graph_index}.txt"
        createGraph(
            cheater_input,
            num_levels,
            num_nodes,
            node_present_probability,
            observing_probability,
            neighbor_probability,
            annotate,
            show_graph=False,
            save_plot=True,
            graph_filename=graph_filename,
            txt_filename_format_one=txt_filename_format_one,
            txt_filename_format_two=txt_filename_format_two,
            neighbor_filename=neighbor_filename,
        )


if __name__ == "__main__":
    # Collect input from the user
    annotate_graph = input("Annotate graphs (y/n): (Default is no) ")
    num_graphs = input("How many graphs would you like to generate: (Default is 50) ")
    cheater_input = input(
        "Enter the probability that a random validator is a cheater: (Default is 0.2) "
    )
    level_input = input(
        "Enter the number of levels/time steps in each graph or type 'r' or 'random' for a random value each iteration: (Default is 10) "
    )
    node_input = input(
        "Enter the number of validator event nodes in each level or type 'r' or 'random' for a random value each iteration: (Default is 5) "
    )
    present_prob_input = input(
        "Enter the probability that an event node is present or type 'r' or 'random' for a random value each iteration: (Default is 0.65) "
    )
    observe_prob_input = input(
        "Enter the probability that an event node observes another validator's event node or type 'r' or 'random' for a random value each iteration: (Default is 0.3) "
    )
    neighbor_prob_input = input(
        "Enter the probability that any two given validators are neighbors or type 'r' or 'random' for a random value each iteration: (Default is 0.5) "
    )
    base_dir = input(
        "Enter the base directory for output files: (Default is current directory) "
    )
    starting_index = input(
        "Enter the starting index for file numbering: (Default is 1) "
    )

    base_dir = "." if not base_dir or base_dir == "" else base_dir

    starting_index = (
        int(starting_index) if starting_index and starting_index != "" else 1
    )

    generate_graphs(
        annotate_graph,
        num_graphs,
        cheater_input,
        level_input,
        node_input,
        present_prob_input,
        observe_prob_input,
        neighbor_prob_input,
        base_dir,
        starting_index,
    )

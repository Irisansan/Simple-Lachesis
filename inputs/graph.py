import networkx as nx
import matplotlib.pyplot as plt
import random
import matplotlib

matplotlib.use("Agg")


def createGraph(
    cheater_probability,
    num_levels,
    num_nodes,
    node_present_probability,
    observing_probability,
    annotate=False,
    show_graph=False,
    save_plot=False,
    graph_filename="graph.png",
    txt_filename_format_one="txt.txt",
    txt_filename_format_two="txt2.txt",
):
    # Initialize the graph
    G = nx.DiGraph()

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

    for i in range(num_levels):
        for j in range(num_nodes):
            if random.random() < node_present_probability:
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
                                # print("CHEATER")
                                # print(node[1]+1, node[0])
                                cheater_nodes[node] = (i - 1, k)
                                target = (i - 1, k)
                                G.add_edge(node, target)
                                break

    # Add edges
    for i in range(1, num_levels):
        for j in range(num_nodes):
            node = (i, j)
            if node in G.nodes and node not in cheater_nodes.keys():
                parent = (i - 1, j)
                self_ref = False
                while not self_ref and parent[0] >= 0:
                    if parent in G.nodes:
                        G.add_edge(node, parent)
                        self_ref = True
                    parent = (parent[0] - 1, parent[1])
                for k in range(num_nodes):
                    if random.random() < observing_probability:
                        target = (i - 1, k)
                        if target in G.nodes:
                            G.add_edge(node, target)

    labels = {
        (i, j): (chr(j + 65), i+1, parent_count[(i, j)]+1)
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
            # color_map[node] = cheater_nodes[node]
            if (i, j) in G.nodes:
                labels[(i, j)] = (chr(deepest_cheater[1] + 65), i + 1, cheating_parents+1)
                cheating_parents += 1
                color_map[(i, j)] = color_map[(deepest_cheater)]

    # [r'$\mathrm{{{}}}_{{{},{}}}$'.format(
    # labels[val][0], labels[val][1], labels[val][2]) for val in labels.keys()]

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
            val: r"$\mathrm{{{}}}_{{{},{}}}$".format(labels[val][0], labels[val][1], labels[val][2]) for val in labels
        },
        font_family="serif",
        font_size=9,
        node_color=[color_map.get(node, color_map[node]) for node in G.nodes()],
        node_size=900,
        font_weight="bold",
    )

    # Adjust figure parameters
    plt.tight_layout()

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
    with open(txt_filename_format_one, "w") as f:
        for node in G:
            f.write("node: (" + str(labels[node][0]) + "," + str(labels[node][1]) + "," + str(labels[node][2]) + ")")
            f.write(";")
            for child in G[node]:
                f.write(
                    " child: ("
                    + str(labels[child][0])
                    + ","
                    + str(labels[child][1])
                    + ","
                    + str(labels[child][2])
                    + ");"
                )
            f.write("\n")

    # Save graph as text data in format two
    with open(txt_filename_format_two, "w") as f:
        for node in G:
            validator = "Event" + labels[node][0]
            epoch = "1"  # affixed to 1 for now
            seq = str(labels[node][2])
            event = validator + seq
            creator = chr(cheater_nodes[node][1] + 65) if node in cheater_nodes.keys() else chr(node[1] + 65)
            node_information = ";".join([event, epoch, seq, creator])
            children_information = ",".join(["Event" + labels[child][0] + str(labels[child][2]) for child in G[node]])

            f.write(node_information + ";" + children_information)
            f.write("\n")

    # Save plot as a PDF
    if save_plot:
        manager = plt.get_current_fig_manager()
        manager.full_screen_toggle()
        fig.savefig(graph_filename, format="pdf", dpi=300, bbox_inches="tight")
    if show_graph:
        plt.show()
    plt.close()


if __name__ == "__main__":
    annotate_graph = input("Annotate graphs (y/n): (Default is no) ")
    if annotate_graph == "y" or annotate_graph == "Y":
        annotate = True
    else:
        annotate = False
    num_graphs = input("How many graphs would you like to generate: (Default is 50) ")
    if num_graphs == "":
        num_graphs = 50
    else:
        num_graphs = int(num_graphs)

    cheater_input = input("Enter the probability that a random validator node is a cheater: (Default is 0.2) ")
    if cheater_input == "":
        cheater_input = 0.2
    else:
        cheater_input = float(cheater_input)

    level_input = input(
        "Enter the number of levels in each graph or type 'r' or 'random' for a random value each iteration: (Default is 10) "
    )
    if level_input.lower() in ["r", "random"]:
        level_input = None
    else:
        if level_input == "":
            level_input = 10
        else:
            level_input = int(level_input)

    node_input = input(
        "Enter the number of nodes in each level or type 'r' or 'random' for a random value each iteration: (Default is 5) "
    )
    if node_input.lower() in ["r", "random"]:
        node_input = None
    else:
        if node_input == "":
            node_input = 5
        else:
            node_input = int(node_input)

    present_prob_input = input(
        "Enter the probability that a node is present or type 'r' or 'random' for a random value each iteration: (Default is 0.65) "
    )
    if present_prob_input.lower() in ["r", "random"]:
        present_prob_input = None
    else:
        if present_prob_input == "":
            present_prob_input = 0.65
        else:
            present_prob_input = float(present_prob_input)

    observe_prob_input = input(
        "Enter the probability that a node observes another validator or type 'r' or 'random' for a random value each iteration: (Default is 0.3) "
    )
    if observe_prob_input.lower() in ["r", "random"]:
        observe_prob_input = None
    else:
        if observe_prob_input == "":
            observe_prob_input = 0.3
        else:
            observe_prob_input = float(observe_prob_input)

    for i in range(num_graphs):
        # print("GRAPH", i+1)
        if level_input is None:
            num_levels = random.randint(5, 100)
        else:
            num_levels = level_input

        if node_input is None:
            num_nodes = random.randint(3, 25)
        else:
            num_nodes = node_input

        if present_prob_input is None:
            node_present_probability = random.uniform(0.5, 0.7)
        else:
            node_present_probability = present_prob_input

        if observe_prob_input is None:
            observing_probability = random.uniform(0.2, 0.4)
        else:
            observing_probability = observe_prob_input

        graph_filename = f"graphs/graph_{i+1}.pdf"
        txt_filename_format_one = f"graphs/graph_{i+1}.txt"
        txt_filename_format_two = f"graphs/events_{i+1}.txt"
        createGraph(
            cheater_input,
            num_levels,
            num_nodes,
            node_present_probability,
            observing_probability,
            annotate,
            show_graph=False,
            save_plot=True,
            graph_filename=graph_filename,
            txt_filename_format_one=txt_filename_format_one,
            txt_filename_format_two=txt_filename_format_two,
        )

import networkx as nx
import matplotlib.pyplot as plt

import networkx as nx
import matplotlib.pyplot as plt


def graph_results(digraph, cheater_list, root_set_nodes, atropos_roots):
    colors = ["orange", "yellow", "blue", "cyan", "purple"]
    cheater_list = [ord(x) - 65 for x in cheater_list]
    root_set_nodes_new = {}
    for key, values in root_set_nodes.items():
        for v in values:
            root_set_nodes_new[(v[0], v[1])] = key

    print(root_set_nodes_new)

    num_levels = 0
    num_nodes = 0
    for node in digraph.nodes:
        print(node, ord(node[0]) - 65, node[1])
        if ord(node[0]) - 65 > num_nodes:
            num_nodes = ord(node[0]) - 65
        if node[1] > num_levels:
            num_levels = node[1]

    print(atropos_roots)

    atropos_roots_new = {}
    for key, value in atropos_roots.items():
        atropos_roots_new[value] = key

    print(root_set_nodes_new)
    print(atropos_roots_new)

    node_colors = {}

    for node in digraph.nodes:
        if node[0] in cheater_list:
            node_colors[node] = "red"
        else:
            node_colors[node] = "gray"
        if node in root_set_nodes_new:
            node_colors[node] = colors[root_set_nodes_new[node] % 5]
        if node in atropos_roots_new:
            node_colors[node] = colors[atropos_roots_new[node] % 5]

    figsize = [20, 10]
    # Scale the figure size proportionally to the number of levels and nodes
    if num_levels >= 15:
        figsize[0] = figsize[0] * num_levels / 20
    if num_nodes >= 10:
        figsize[0] = figsize[0] * num_nodes / 4
        figsize[1] = figsize[1] * num_nodes / 10

    pos = {}

    fig = plt.figure(figsize=(figsize[0], figsize[1]))
    for i in range(num_nodes + 1):
        for j in range(num_levels + 1):
            node = (chr(i + 65), j)
            pos[node] = (j, i)

    print(pos[("B", 4)])

    nx.draw(
        digraph,
        pos,
        font_family="serif",
        font_size=9,
        node_size=900,
        font_weight="bold",
    )

    # Adjust figure parameters
    plt.tight_layout()
    plt.show()

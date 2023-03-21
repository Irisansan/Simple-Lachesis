import networkx as nx
import matplotlib.pyplot as plt


def graph_results(digraph, cheater_list, root_set_nodes, atropos_roots):
    colors = ["orange", "yellow", "blue", "cyan", "purple"]
    cheater_list = [ord(x) - 65 for x in cheater_list]
    root_set_nodes_new = {}
    for key, values in root_set_nodes.items():
        for v in values:
            root_set_nodes_new[(v[0], v[1])] = key

    num_levels = 0
    num_nodes = 0
    for node in digraph.nodes:
        if ord(node[0]) - 65 > num_nodes:
            num_nodes = ord(node[0]) - 65
        if node[1] > num_levels:
            num_levels = node[1]

    atropos_roots_new = {}
    max_decided_frame = max([root for root in atropos_roots])
    for key, value in atropos_roots.items():
        atropos_roots_new[value] = key

    node_colors = {}
    node_frames = {}

    bad_nodes = []
    for node in digraph.nodes:
        if ord(node[0]) - 65 in cheater_list:
            bad_nodes.append(node)
        else:
            node_colors[node] = "#666699"
            node_frames[node] = digraph.nodes.get(node)["frame"]
        if node in root_set_nodes_new:
            node_colors[node] = colors[root_set_nodes_new[node] % 5]
            node_frames[node] = digraph.nodes.get(node)["frame"]
        if node in atropos_roots_new:
            node_colors[node] = "#66ff99"
            node_frames[node] = digraph.nodes.get(node)["frame"]

    digraph.remove_nodes_from(bad_nodes)

    pos = {}

    figsize = [20, 10]
    # Scale the figure size proportionally to the number of levels and nodes
    if num_levels >= 15:
        figsize[0] = figsize[0] * num_levels / 20
    if num_nodes >= 10:
        figsize[0] = figsize[0] * num_nodes / 4
        figsize[1] = figsize[1] * num_nodes / 10

    fig = plt.figure(figsize=(figsize[0], figsize[1]))
    for i in range(num_nodes + 1):
        for j in range(num_levels + 1):
            node = (chr(i + 65), j)
            pos[node] = (j, i)

    for frame in set(node_frames.values()):
        nodes_in_frame = [node for node in node_frames if node_frames[node] == frame]
        min_x, min_y, max_x, max_y = float("inf"), float("inf"), float("-inf"), float("-inf")
        for node in nodes_in_frame:
            x, y = pos[node]
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
        rect = plt.Rectangle(
            (min_x - 0.5, min_y - 0.5),
            max_x - min_x + 1,
            max_y - min_y + 1,
            edgecolor=colors[frame % 5],
            facecolor="none",
        )

        plt.gca().add_patch(rect)
        rect_x, rect_y = rect.get_xy()
        frame_text = r"$\mathrm{{block}}\ {}$".format(frame)
        if frame > max_decided_frame:
            frame_text = r"$\mathrm{{frame}}\ {}$".format(frame)
        plt.text(
            rect_x + 0.2,
            rect_y + 0.2,
            frame_text,
            ha="center",
            va="center",
            fontsize=10,
            rotation=0,
        )

    labels = {
        (chr(i + 65), j): (chr(i + 65), j, digraph.nodes.get((chr(i + 65), j))["predecessors"])
        for i in range(num_nodes + 1)
        for j in range(num_levels + 1)
        if (chr(i + 65), j) in digraph.nodes
    }

    nx.draw(
        digraph,
        pos,
        with_labels=True,
        labels={
            val: r"$\mathrm{{{}}}_{{{},{}}}$".format(labels[val][0], labels[val][1], labels[val][2]) for val in labels
        },
        font_family="serif",
        font_size=9,
        node_size=900,
        node_color=[node_colors.get(node, node_colors[node]) for node in digraph.nodes()],
        font_weight="bold",
    )

    # Adjust figure parameters
    plt.tight_layout()
    save_plot = True

    # Save plot as a PDF
    if save_plot:
        manager = plt.get_current_fig_manager()
        manager.full_screen_toggle()
        fig.savefig("results.pdf", format="pdf", dpi=300, bbox_inches="tight")

    plt.close()

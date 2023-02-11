import networkx as nx
import matplotlib.pyplot as plt
import random
import matplotlib
matplotlib.use('Agg')

def createGraph(num_levels, num_nodes, node_present_probability, observing_probability, show_graph=False, save_plot=False, filename='plot.png'):
    # Initialize the graph
    G = nx.DiGraph()

    # Add nodes and assign colors
    colors = ['red', 'green', 'blue', 'purple', 'orange', 'brown', 'pink', 'gray', 'olive', 'cyan']
    color_map = {}

    for i in range(num_levels):
        for j in range(num_nodes):
            if random.random() < node_present_probability:
                node = (i, j)
                G.add_node(node)
                if i == 0:
                    color_map[node] = colors[j % len(colors)]
                else:
                    parent = (i-1, j)
                    self_ref = False
                    while not self_ref and parent[0]>=0:
                        if parent in G.nodes:
                            if parent in color_map:
                                color_map[node] = color_map[parent]
                            else:
                                color_map[node] = random.choice(colors)
                            G.add_edge(node, parent)
                            self_ref = True
                        parent = (parent[0]-1, parent[1])
                if node not in color_map:
                    color_map[node] = random.choice(colors)

    # Add edges
    for i in range(1, num_levels):
        for j in range(num_nodes):
            node = (i, j)
            if node in G.nodes:
                parent = (i-1, j)
                self_ref = False
                while not self_ref and parent[0]>=0:
                    if parent in G.nodes:
                        G.add_edge(node, parent)
                        self_ref = True
                    parent = (parent[0]-1, parent[1])
                for k in range(num_nodes):
                    if random.random() < observing_probability:
                        target = (i-1, k)
                        if target in G.nodes:
                            G.add_edge(node, target)

    # Plot the graph
    fig = plt.figure(figsize=(20, 10))
    pos = {(i, j): (i, j) for i in range(num_levels) for j in range(num_nodes)}
    labels = {(i, j): r'${}_{{{}}}$'.format(j+1, i) for i in range(num_levels) for j in range(num_nodes) if (i, j) in G.nodes}
    nx.draw(G, pos, with_labels=True, labels=labels, font_family='serif', node_color=[color_map.get(node, color_map[node]) for node in G.nodes()], node_size=800, font_weight='bold')
    if save_plot:
        manager = plt.get_current_fig_manager()
        manager.full_screen_toggle()
        fig.savefig(filename) 
    if show_graph:
        plt.show()
    plt.close()

if __name__ == "__main__":
    num_graphs = input("How many graphs would you like to generate: (Default is 50) ")
    if num_graphs=='':
        num_graphs=50
    else:
        num_graphs=int(num_graphs)
    
    level_input = input("Enter the number of levels in each graph or type 'r' or 'random' for a random value each iteration: (Default is 10) ")
    if level_input.lower() in ['r', 'random']:
        level_input = None
    else:
        if level_input=='':
            level_input=10
        else:
            level_input = int(level_input)

    node_input = input("Enter the number of nodes in each level or type 'r' or 'random' for a random value each iteration: (Default is 5) ")
    if node_input.lower() in ['r', 'random']:
        node_input = None
    else:
        if node_input=='':
            node_input=5
        else:
            node_input = int(node_input)

    present_prob_input = input("Enter the probability that a node is present or type 'r' or 'random' for a random value each iteration: (Default is 0.65) ")
    if present_prob_input.lower() in ['r', 'random']:
        present_prob_input = None
    else:
        if present_prob_input=='':
            present_prob_input=0.65
        else:
            present_prob_input = float(present_prob_input)

    observe_prob_input = input("Enter the probability that a node observes another validator or type 'r' or 'random' for a random value each iteration: (Default is 0.3) ")
    if observe_prob_input.lower() in ['r', 'random']:
        observe_prob_input = None
    else:
        if observe_prob_input=='':
            observe_prob_input=0.3
        else:
            observe_prob_input = float(observe_prob_input)

    for i in range(num_graphs):
        if level_input is None:
            num_levels = random.randint(3, 50)
        else:
            num_levels = level_input

        if node_input is None:
            num_nodes = random.randint(3, 10)
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

        filename = f'graphs/graph_{i+1}.png'
        createGraph(num_levels, num_nodes, node_present_probability, observing_probability, show_graph=False, save_plot=True, filename=filename)


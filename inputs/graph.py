import networkx as nx
import matplotlib.pyplot as plt
import random

# Initialize the graph
G = nx.DiGraph()

# Define the number of levels and the number of nodes on each level
num_levels = random.randint(5, 10)
num_nodes = random.randint(3, 9)

# Define the probability that a node is present
node_present_probability = 0.65

# Define the probability that a node observes validators at a prior level
observing_probability = 0.3

# Add nodes
for i in range(num_levels):
    for j in range(num_nodes):
        if random.random() < node_present_probability:
            G.add_node((i, j))

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
pos = {(i, j): (i, j) for i in range(num_levels) for j in range(num_nodes)}
nx.draw(G, pos, with_labels=True)
plt.show()


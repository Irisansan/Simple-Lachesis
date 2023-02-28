import DAG as dag
import glob

'''
#iterating over all graphs as part of testing, etc.
graphs_directory = "inputs/graphs/graph_*.txt"

for filename in glob.glob(graphs_directory):
    graph = dag.convert_input_to_DAG(filename)
'''

# graph = G
G = dag.convert_input_to_DAG("inputs/graphs/graph_10.txt")

print("Nodes in the graph:")
for node in G.nodes(data=True):
    print(node)

print("Edges in the graph:")
for edge in G.edges():
    print(edge)

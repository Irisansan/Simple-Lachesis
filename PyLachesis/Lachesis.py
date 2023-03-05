import DAG as dag
import glob
import networkx as nx

"""
#iterating over all graphs as part of testing, etc.
graphs_directory = "inputs/graphs/graph_*.txt"

for filename in glob.glob(graphs_directory):
    graph = dag.convert_input_to_DAG(filename)
"""


class Lachesis:
    # state of Lachesis
    def __init__(self, validator=None):
        self.block = 0
        self.frame = 0
        self.epoch = 0
        self.root_set = []
        self.cheater_list = []
        self.atropos_list = []
        self.validator = validator
        self.adjacency_matrix = []
        self.time = 0
        self.global_vector = []
        self.events_at_step = []
        # combining DAGs will eventually be required
        self.local_dag = nx.DiGraph()

    def check_for_roots(self):
        return

    """
    def elect_atropos(self):

    def forkless_cause(self):
    
    def communicate_with_neighbors(self):
    """


# Lachesis will eventually run for every node/validator, each of which
# will have a limited view of the test DAG we are using, for now we run
# Lachesis on one node
def process_graph_by_timesteps(graph):
    lachesis_state = Lachesis()
    nodes = iter(graph.nodes(data=True))
    node = next(nodes, None)
    timestep_graph = nx.DiGraph()  # initialize the minigraph
    while node is not None:
        validator = node[0][0]
        timestamp = node[0][1]
        if timestamp == lachesis_state.time:
            # add node to the minigraph
            timestep_graph.add_node((validator, timestamp))
            # add outward edges to the minigraph
            for source, target in graph.out_edges((validator, timestamp)):
                timestep_graph.add_edge(source, target)
            node = next(nodes, None)
        else:
            # end of timestep, combine minigraph with local_dag
            lachesis_state.local_dag = nx.compose(
                lachesis_state.local_dag, timestep_graph
            )
            lachesis_state.time += 1
            timestep_graph = nx.DiGraph()  # reset the minigraph
    # combine the last minigraph with local_dag
    # (in case the graph didn't end on a timestep)
    lachesis_state.local_dag = nx.compose(lachesis_state.local_dag, timestep_graph)
    # print(lachesis_state.local_dag.edges())  # print the edges of local_dag
    # print(lachesis_state.local_dag.nodes())  # print the nodes of local_dag


if __name__ == "__main__":
    # graph = G
    G = dag.convert_input_to_DAG("inputs/graphs/graph_10.txt")
    process_graph_by_timesteps(G)

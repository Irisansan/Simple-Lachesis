import DAG as dag
import glob

'''
#iterating over all graphs as part of testing, etc.
graphs_directory = "inputs/graphs/graph_*.txt"

for filename in glob.glob(graphs_directory):
    graph = dag.convert_input_to_DAG(filename)
'''


class Lachesis:
    # state of Lachesis
    def __init__(self):
        self.atropos_list = 0
        self.block = 0
        self.epoch = 0
        self.cheater_list = []
        self.time = 0

    def increment_time(self):
        self.time += 1


def process_graph_by_timesteps(graph):
    lachesis_state = Lachesis()
    nodes = iter(graph.nodes(data=True))
    node = next(nodes, None)
    while node is not None:
        validator = node[0][0]
        timestamp = node[0][1]
        predecessors = node[1]['predecessors']
        if timestamp == lachesis_state.time:
            print("validator:", validator, "timestamp:",
                  timestamp, "predecessors:", predecessors)
            node = next(nodes, None)
        else:
            lachesis_state.increment_time()


'''
to do:

def check_for_roots
def elect_atropos:
def forkless_cause:

'''


if __name__ == "__main__":
    # graph = G
    G = dag.convert_input_to_DAG("inputs/graphs/graph_10.txt")
    process_graph_by_timesteps(G)

import glob
import os
from tqdm import tqdm
from lachesis import Lachesis, LachesisMultiInstance

import os


def create_dir(path):
    try:
        os.makedirs(path)
    except FileExistsError:
        # directory already exists
        pass


def automate_lachesis(input_dir, output_dir, create_graph=False):
    input_graphs_directory = os.path.join(input_dir, "graph_*.txt")
    file_list = glob.glob(input_graphs_directory)

    print(f"processing {len(file_list)} files...")

    for _, input_filename in tqdm(
        enumerate(file_list), total=len(file_list), desc="processing files"
    ):
        base_filename = os.path.basename(input_filename)
        graph_name = base_filename[
            base_filename.index("_") + 1 : base_filename.index(".txt")
        ]

        # create a directory for each graph
        graph_dir = os.path.join(output_dir, f"graph_{graph_name}_results")
        create_dir(graph_dir)

        output_filename = os.path.join(graph_dir, "result.pdf")

        # Single instance run
        lachesis_state = Lachesis()
        lachesis_state.run_lachesis(input_filename, output_filename, create_graph)

        # Multiinstance run
        lachesis_multi_instance = LachesisMultiInstance(graph_results=create_graph)
        lachesis_multi_instance.run_lachesis_multiinstance(input_filename, graph_dir)


print("\nautomating graphs without cheaters...\n\n")
automate_lachesis("../inputs/graphs", "../inputs/results", True)
print("\n\nautomating graphs with cheaters...\n\n")
automate_lachesis("../inputs/cheaters", "../inputs/cheater_results", True)

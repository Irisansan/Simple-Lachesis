import glob
import os
from tqdm import tqdm
from lachesis import Lachesis, LachesisMultiInstance


def create_dir(path):
    try:
        os.makedirs(path)
    except FileExistsError:
        pass


def automate_lachesis(input_dir, output_dir, create_graph=False):
    input_graphs_directory = os.path.join(input_dir, "graph_*.txt")
    file_list = glob.glob(input_graphs_directory)

    print(f"processing {len(file_list)} files...")

    success_count = 0

    for _, input_filename in tqdm(
        enumerate(file_list), total=len(file_list), desc="processing files"
    ):
        try:
            base_filename = os.path.basename(input_filename)
            graph_name = base_filename[
                base_filename.index("_") + 1 : base_filename.index(".txt")
            ]

            graph_dir = os.path.join(output_dir, f"graph_{graph_name}_results")
            create_dir(graph_dir)

            output_filename = os.path.join(graph_dir, "result.pdf")

            lachesis_state = Lachesis()
            lachesis_state.run_lachesis(input_filename, output_filename, create_graph)

            lachesis_multi_instance = LachesisMultiInstance(graph_results=create_graph)
            lachesis_multi_instance.run_lachesis_multiinstance(
                input_filename, graph_dir
            )

            success_count += 1

        except Exception as e:
            print("error in", graph_name, str(e))

    success_rate = success_count / len(file_list) * 100
    print(f"success rate: {success_rate:.1f}%")


print("\nautomating graphs without cheaters...\n\n")
automate_lachesis("../inputs/graphs", "../inputs/results", False)
print("\n\nautomating graphs with cheaters...\n\n")
automate_lachesis("../inputs/cheaters", "../inputs/cheaters", False)

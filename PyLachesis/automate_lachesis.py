import glob
import os
from tqdm import tqdm
from lachesis import Lachesis

print("automating lachesis runs...")
print()


def automate_lachesis(input_dir, output_dir, create_graph=False):
    input_graphs_directory = os.path.join(input_dir, "graph_*.txt")
    print(input_graphs_directory)
    file_list = glob.glob(input_graphs_directory)

    print("file count", len(file_list))

    for _, input_filename in tqdm(
        enumerate(file_list), total=len(file_list), desc="Processing files"
    ):
        base_filename = os.path.basename(input_filename)
        graph_name = base_filename[
            base_filename.index("_") + 1 : base_filename.index(".txt")
        ]
        output_filename = os.path.join(output_dir, f"result_{graph_name}.pdf")
        lachesis_state = Lachesis()

        # can store results for later in a different format...
        results = lachesis_state.run_lachesis(
            input_filename, output_filename, create_graph
        )


# automate_lachesis("../inputs/graphs", "../inputs/results", True)
automate_lachesis(
    "../inputs/graphs_with_cheaters", "../inputs/results_with_cheaters", True
)
# automate_lachesis(
#     "../inputs/graphs_with_networks",
#     "../inputs/results_with_networks",
#     True,
# )
automate_lachesis(
    "../inputs/graphs_with_networks_and_cheaters",
    "../inputs/results_with_networks_and_cheaters",
    True,
)

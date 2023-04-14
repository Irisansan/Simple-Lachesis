from tqdm import tqdm
from graph import generate_graphs

parameters_list = [
    ("graphs_with_networks", "y", 25, 1, 50, 4, 0.65, 0.35, 0.6, 0),
    ("graphs_with_networks", "y", 25, 26, 50, 5, 0.65, 0.35, 0.6, 0),
    ("graphs_with_networks", "y", 50, 51, "r", "r", 0.65, 0.35, 0.6, 0),
    (
        "graphs_with_networks_and_cheaters",
        "y",
        25,
        1,
        50,
        4,
        0.65,
        0.35,
        0.6,
        0.25,
    ),
    (
        "graphs_with_networks_and_cheaters",
        "y",
        25,
        26,
        50,
        5,
        0.65,
        0.35,
        0.6,
        0.25,
    ),
    (
        "graphs_with_networks_and_cheaters",
        "y",
        50,
        51,
        "r",
        "r",
        0.65,
        0.35,
        0.6,
        0.25,
    ),
]

total_graphs = sum([p[2] for p in parameters_list])

with tqdm(total=total_graphs, desc="Progress", unit="graph") as progress_bar:
    for parameters in parameters_list:
        (
            base_dir,
            annotate_graph,
            num_graphs,
            starting_index,
            level_input,
            node_input,
            present_prob,
            observe_prob_input,
            neighbor_prob_input,
            cheater_input,
        ) = parameters

        for _ in range(num_graphs):
            generate_graphs(
                annotate_graph,
                1,
                cheater_input,
                level_input,
                node_input,
                present_prob,
                observe_prob_input,
                neighbor_prob_input,
                base_dir,
                starting_index,
            )
            starting_index += 1
            progress_bar.update(1)

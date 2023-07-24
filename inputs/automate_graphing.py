from tqdm import tqdm
from graph import generate_graphs

parameters_list = [
    ("y", "20", "0", "20", "4", "0.65", "0.4", "0.5", "./graphs", "1"),
    ("y", "20", "0", "20", "5", "0.65", "0.4", "0.5", "./graphs", "21"),
    ("y", "960", "0", "r", "r", "r", "r", "r", "./graphs", "41"),
    ("y", "20", "0.3", "20", "4", "0.65", "0.4", "0.5", "./cheaters", "1"),
    ("y", "20", "0.3", "20", "5", "0.65", "0.4", "0.5", "./cheaters", "21"),
    ("y", "960", "0.3", "r", "r", "r", "r", "r", "./cheaters", "41"),
]

total_graphs = sum([int(p[1]) for p in parameters_list])

print()
print("automating graphing...")
print()

with tqdm(total=total_graphs, desc="Progress", unit="graph") as progress_bar:
    for parameters in parameters_list:
        generate_graphs(
            parameters[0],
            parameters[1],
            parameters[2],
            parameters[3],
            parameters[4],
            parameters[5],
            parameters[6],
            parameters[7],
            parameters[8],
            parameters[9],
        )
        progress_bar.update(int(parameters[1]))

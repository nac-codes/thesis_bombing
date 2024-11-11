import networkx as nx
import random
import matplotlib.pyplot as plt
from typing import List, Tuple

class WarfareNetwork:
    def __init__(self, num_nodes: int, num_edges: int, workers_per_node: int):
        self.G = nx.gnm_random_graph(num_nodes, num_edges, directed=True)
        self.workers = {node: workers_per_node for node in self.G.nodes()}
        self.replacement_workers = workers_per_node * num_nodes
        self.node_capacity = {node: 1.0 for node in self.G.nodes()}
        self.edge_capacity = {edge: 1.0 for edge in self.G.edges()}

    def calculate_network_output(self) -> float:
        return sum(self.node_capacity[node] * (self.workers[node] / 100) for node in self.G.nodes())

    def precision_bombing(self, num_targets: int):
        targets = random.sample(list(self.G.nodes()) + list(self.G.edges()), min(num_targets, len(self.G.nodes()) + len(self.G.edges())))
        for target in targets:
            if isinstance(target, int):  # Node
                self.node_capacity[target] = 0.0  
            else:  # Edge
                self.edge_capacity[target] = 0.0  

    def area_bombing(self, num_targets: int):
        # number of targets is the number of workers / 10 / 2
        num_workers = num_targets * 10
        targets = random.sample(list(self.G.nodes()) + list(self.G.edges()), num_targets)
        for target in targets:
            if isinstance(target, int):  # Node
                self.node_capacity[target] = 0.0  
            else:  # Edge
                self.edge_capacity[target] = 0.0  

        workers_to_remove = min(num_workers, sum(self.workers.values()) + self.replacement_workers)
        while workers_to_remove > 0:
            if self.replacement_workers > 0:
                remove_from_replacement = min(workers_to_remove, self.replacement_workers)
                self.replacement_workers -= remove_from_replacement
                workers_to_remove -= remove_from_replacement
            else:
                node = random.choice(list(self.G.nodes()))
                remove_from_node = min(workers_to_remove, self.workers[node])
                self.workers[node] -= remove_from_node
                workers_to_remove -= remove_from_node

    def repair_and_replenish(self):
        # Repair nodes and edges
        for node in self.G.nodes():
            self.node_capacity[node] = min(1.0, self.node_capacity[node] + 0.1)
        for edge in self.G.edges():
            self.edge_capacity[edge] = min(1.0, self.edge_capacity[edge] + 0.1)

        # Replenish workers
        for node in self.G.nodes():
            if self.workers[node] < 100 and self.replacement_workers > 0:
                workers_to_add = min(100 - self.workers[node], self.replacement_workers)
                self.workers[node] += workers_to_add
                self.replacement_workers -= workers_to_add

        # Grow replacement workers
        self.replacement_workers = min(self.replacement_workers * 1.05, 100 * len(self.G.nodes()))

def run_simulation(network: WarfareNetwork, max_turns: int, strategy: str) -> List[float]:
    outputs = []
    for turn in range(max_turns):
        bombing_effect = 5 + turn // 10  # Slight increase over time
        
        if strategy == "precision":
            network.precision_bombing(bombing_effect)
        else:
            network.area_bombing(bombing_effect)
        
        network.repair_and_replenish()
        output = network.calculate_network_output()
        outputs.append(output)
        
        if output < 0.01:  # Stop if output is essentially zero
            break
    
    return outputs

def plot_results(precision_results: List[float], area_results: List[float]):
    plt.figure(figsize=(12, 8))  # Increased size for better visibility
    plt.plot(precision_results, label='Precision Bombing', color='blue', linewidth=2)  # Added color and linewidth
    plt.plot(area_results, label='Area Bombing', color='orange', linewidth=2)  # Added color and linewidth
    plt.xlabel('Turns', fontsize=14)  # Increased font size
    plt.ylabel('Network Output', fontsize=14)  # Increased font size
    plt.title('Precision vs Area Bombing Effectiveness', fontsize=16)  # Increased font size
    plt.legend(fontsize=12)  # Increased font size for legend
    plt.grid(True, linestyle='--', alpha=0.7)  # Changed grid style for better detail
    
    # save the plot
    plt.savefig('precision_vs_area_bombing.png', dpi=300)  # Increased DPI for better quality


# Run simulation
num_nodes, num_edges, workers_per_node = 1000, 4000, 100
max_turns = 1000

precision_results = run_simulation(WarfareNetwork(num_nodes, num_edges, workers_per_node), max_turns, "precision")
area_results = run_simulation(WarfareNetwork(num_nodes, num_edges, workers_per_node), max_turns, "area")

# Plot results
plot_results(precision_results, area_results)

# Print the number of turns until network output reached near-zero
print(f"Precision bombing reduced output to near-zero after {len(precision_results)} turns")
print(f"Area bombing reduced output to near-zero after {len(area_results)} turns")
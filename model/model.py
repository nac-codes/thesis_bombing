import networkx as nx
import random
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Set
from dataclasses import dataclass
from collections import defaultdict
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.DEBUG)

@dataclass
class SimulationStats:
    turn: int
    network_output: float
    total_workers: int
    replacement_workers: int
    destroyed_nodes: int
    damaged_nodes: int
    destroyed_edges: int
    damaged_edges: int
    workers_killed: int
    avg_node_capacity: float
    avg_edge_capacity: float
    avg_workers_per_node: float
    endpoint_outputs: Dict[int, float]  # New: track individual endpoint outputs

class WarfareNetwork:
    def __init__(self, num_nodes: int, num_edges: int, workers_per_node: int = 10):
        # Initialize network
        logging.debug(f"Initializing WarfareNetwork with {num_nodes} nodes and {num_edges} edges.")
        self.G = nx.gnm_random_graph(num_nodes, num_edges, directed=True)
        self.workers = {node: workers_per_node for node in self.G.nodes()}
        self.max_workers = workers_per_node
        self.initial_workers = workers_per_node * num_nodes
        self.replacement_workers = self.initial_workers
        self.node_capacity = {node: 1.0 for node in self.G.nodes()}
        self.edge_capacity = {edge: 1.0 for edge in self.G.edges()}
        self.total_workers_killed = 0
        
        # Identify endpoint nodes (nodes with no outgoing edges)
        self.endpoint_nodes = [node for node in self.G.nodes() 
                             if self.G.out_degree(node) == 0]
        logging.debug(f"Identified endpoint nodes: {self.endpoint_nodes}")
        
        # Cache for paths to endpoints
        self._path_cache = self._build_path_cache()

    def _build_path_cache(self) -> Dict[int, List[List[int]]]:
        """Build cache of all paths to each endpoint with optimizations"""
        logging.debug("Building path cache for endpoints.")
        cache = {}
        
        for endpoint in self.endpoint_nodes:
            # Create a subgraph of nodes that can reach this endpoint
            # First, reverse the graph to find predecessors
            pred = nx.predecessor(self.G, endpoint)
            reachable_nodes = set(pred.keys())
            
            # Create subgraph of only relevant nodes
            subgraph = self.G.subgraph(reachable_nodes)
            
            # Limit path length to prevent exponential explosion
            MAX_PATH_LENGTH = 5  # Adjust this value based on your needs
            all_paths = []
            
            for node in reachable_nodes:
                if node != endpoint:
                    try:
                        # Use a generator and limit the number of paths per node
                        paths = list(nx.all_simple_paths(
                            subgraph, 
                            node, 
                            endpoint, 
                            cutoff=MAX_PATH_LENGTH
                        ))
                        # Limit the number of paths per node if needed
                        MAX_PATHS_PER_NODE = 10  # Adjust based on needs
                        all_paths.extend(paths[:MAX_PATHS_PER_NODE])
                    except nx.NetworkXNoPath:
                        continue
            
            cache[endpoint] = all_paths
            logging.debug(f"Cached {len(all_paths)} paths for endpoint {endpoint}.")
        
        return cache

    def calculate_path_value(self, path: List[int]) -> float:
        """Calculate the cascading value of a path based on node capacities"""
        value = 1.0
        for node in path:
            value *= self.node_capacity[node]
            # If any node is completely destroyed, the whole path is worthless
            if value == 0:
                logging.debug(f"Path {path} is worthless due to destroyed node.")
                return 0
        logging.debug(f"Calculated path value for {path}: {value}")
        return value

    def calculate_network_output(self) -> Tuple[float, Dict[int, float]]:
        """Calculate total network output and individual endpoint outputs"""
        total_output = 0.0
        endpoint_outputs = {}
        
        for endpoint in self.endpoint_nodes:
            all_paths = self._path_cache[endpoint]
            
            # Calculate unique nodes in all paths to this endpoint
            unique_nodes = set()
            for path in all_paths:
                unique_nodes.update(path)
            
            # Calculate the value of each path and sum them
            path_values = sum(self.calculate_path_value(path) for path in all_paths)
            
            # Calculate endpoint output weighted by number of unique nodes
            if all_paths:  # Only if there are paths to this endpoint
                endpoint_output = path_values * len(unique_nodes)
                endpoint_outputs[endpoint] = endpoint_output
                total_output += endpoint_output
                logging.debug(f"Endpoint {endpoint} output: {endpoint_output}")
            else:
                endpoint_outputs[endpoint] = 0.0
        
        logging.debug(f"Total network output calculated: {total_output}")
        return total_output, endpoint_outputs

    def precision_bombing(self, num_targets: int) -> Tuple[int, int]:
        """Precision bombing targets specific nodes/edges"""
        logging.debug(f"Executing precision bombing with {num_targets} targets.")
        targets = random.sample(list(self.G.nodes()) + list(self.G.edges()), 
                              min(num_targets, len(self.G.nodes()) + len(self.G.edges())))
        nodes_hit = 0
        edges_hit = 0
        
        for target in targets:
            if isinstance(target, int):  # Node
                damage = random.uniform(0.5, 1.0)  # Variable damage
                self.node_capacity[target] *= max(0, 1 - damage)
                nodes_hit += 1
                logging.debug(f"Node {target} hit with damage {damage}. New capacity: {self.node_capacity[target]}")
            else:  # Edge
                damage = random.uniform(0.5, 1.0)
                self.edge_capacity[target] *= max(0, 1 - damage)
                edges_hit += 1
                logging.debug(f"Edge {target} hit with damage {damage}. New capacity: {self.edge_capacity[target]}")
                
        return nodes_hit, edges_hit

    def area_bombing(self, num_targets: int) -> Tuple[int, int, int]:
        """Area bombing affects infrastructure and workers"""
        logging.debug(f"Executing area bombing with {num_targets} targets.")
        num_workers_per_target = 5  # Reduced worker casualties
        nodes_hit, edges_hit = self.precision_bombing(num_targets)
        
        # Handle worker casualties
        workers_killed = 0
        max_workers_to_remove = min(
            num_targets * num_workers_per_target,
            int((sum(self.workers.values()) + self.replacement_workers) * 0.1)  # Max 10% casualties
        )
        
        workers_to_remove = max_workers_to_remove
        
        while workers_to_remove > 0:
            if self.replacement_workers > 0:
                remove_from_replacement = min(workers_to_remove, self.replacement_workers)
                self.replacement_workers -= remove_from_replacement
                workers_to_remove -= remove_from_replacement
                workers_killed += remove_from_replacement
                logging.debug(f"Removed {remove_from_replacement} workers from replacement pool.")
            else:
                node = random.choice(list(self.G.nodes()))
                remove_from_node = min(workers_to_remove, self.workers[node])
                self.workers[node] -= remove_from_node
                workers_to_remove -= remove_from_node
                workers_killed += remove_from_node
                logging.debug(f"Removed {remove_from_node} workers from node {node}.")
        
        self.total_workers_killed += workers_killed
        logging.debug(f"Total workers killed in area bombing: {workers_killed}")
        return nodes_hit, edges_hit, workers_killed

    def repair_and_replenish(self):
        """Handle repairs and worker replenishment"""
        logging.debug("Repairing and replenishing workers.")
        # Repair nodes based on worker count
        for node in self.G.nodes():
            if self.node_capacity[node] < 1.0 and self.workers[node] > 0:
                worker_efficiency = self.workers[node] / self.max_workers
                repair_amount = 0.25 * worker_efficiency * (1.0 - self.node_capacity[node])
                self.node_capacity[node] = min(1.0, self.node_capacity[node] + repair_amount)
                logging.debug(f"Node {node} repaired by {repair_amount}. New capacity: {self.node_capacity[node]}")

        # Repair edges (slower than nodes)
        for edge in self.G.edges():
            if self.edge_capacity[edge] < 1.0:
                repair_amount = 0.1 * (1.0 - self.edge_capacity[edge])
                self.edge_capacity[edge] = min(1.0, self.edge_capacity[edge] + repair_amount)
                logging.debug(f"Edge {edge} repaired by {repair_amount}. New capacity: {self.edge_capacity[edge]}")

        # Replenish workers (daily growth rate of 2%/365)
        daily_growth_rate = 0.02 / 365
        total_current_workers = sum(self.workers.values()) + self.replacement_workers
        
        if total_current_workers < self.initial_workers:
            new_workers = int(total_current_workers * daily_growth_rate)
            self.replacement_workers += new_workers
            logging.debug(f"Replenished {new_workers} workers to replacement pool.")

        # Distribute replacement workers
        for node in self.G.nodes():
            if self.workers[node] < self.max_workers and self.replacement_workers > 0:
                workers_needed = self.max_workers - self.workers[node]
                workers_added = min(workers_needed, self.replacement_workers)
                self.workers[node] += workers_added
                self.replacement_workers -= workers_added
                logging.debug(f"Added {workers_added} workers to node {node}. Total now: {self.workers[node]}")

    def get_statistics(self, turn: int) -> SimulationStats:
        """Gather current simulation statistics"""
        total_workers = sum(self.workers.values())
        destroyed_nodes = sum(1 for cap in self.node_capacity.values() if cap == 0.0)
        damaged_nodes = sum(1 for cap in self.node_capacity.values() if 0.0 < cap < 1.0)
        destroyed_edges = sum(1 for cap in self.edge_capacity.values() if cap == 0.0)
        damaged_edges = sum(1 for cap in self.edge_capacity.values() if 0.0 < cap < 1.0)
        
        network_output, endpoint_outputs = self.calculate_network_output()
        
        logging.debug(f"Gathered statistics for turn {turn}.")
        return SimulationStats(
            turn=turn,
            network_output=network_output,
            total_workers=total_workers,
            replacement_workers=self.replacement_workers,
            destroyed_nodes=destroyed_nodes,
            damaged_nodes=damaged_nodes,
            destroyed_edges=destroyed_edges,
            damaged_edges=damaged_edges,
            workers_killed=self.total_workers_killed,
            avg_node_capacity=sum(self.node_capacity.values()) / len(self.node_capacity),
            avg_edge_capacity=sum(self.edge_capacity.values()) / len(self.edge_capacity),
            avg_workers_per_node=total_workers / len(self.G.nodes()),
            endpoint_outputs=endpoint_outputs
        )

def run_simulation(network: WarfareNetwork, max_turns: int, strategy: str) -> List[SimulationStats]:
    """Run the simulation with specified strategy"""
    stats_history = []
    
    for turn in tqdm(range(max_turns), desc="Running Simulation"):
        # Calculate bombing effect (more gradual increase)
        bombing_effect = 3 + turn // 20  # Slower escalation
        logging.debug(f"Turn {turn}: Bombing effect is {bombing_effect}.")
        
        if strategy == "precision":
            network.precision_bombing(bombing_effect)
        else:
            network.area_bombing(bombing_effect)
        
        network.repair_and_replenish()
        stats = network.get_statistics(turn)
        stats_history.append(stats)
        
        # Modified victory condition (less than 10% of initial output)
        if stats.network_output < network.initial_workers * 0.1:
            logging.debug(f"Victory condition met at turn {turn}. Network output: {stats.network_output}")
            break
    
    return stats_history

def plot_detailed_results(precision_stats: List[SimulationStats], area_stats: List[SimulationStats]):
    """Generate detailed visualization of simulation results"""
    fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2, figsize=(20, 24))
    
    turns_p = [stat.turn for stat in precision_stats]
    turns_a = [stat.turn for stat in area_stats]
    
    # Plot 1: Network Output
    ax1.plot(turns_p, [stat.network_output for stat in precision_stats], 
             label='Precision', color='blue', linewidth=2)
    ax1.plot(turns_a, [stat.network_output for stat in area_stats], 
             label='Area', color='red', linewidth=2)
    ax1.set_title('Network Output Over Time')
    ax1.set_xlabel('Turns')
    ax1.set_ylabel('Output')
    ax1.grid(True)
    ax1.legend()

    # Plot 2: Worker Statistics
    ax2.plot(turns_p, [stat.total_workers for stat in precision_stats], 
             label='Precision - Active', color='blue', linewidth=2)
    ax2.plot(turns_p, [stat.replacement_workers for stat in precision_stats], 
             label='Precision - Reserve', color='blue', linestyle='--')
    ax2.plot(turns_a, [stat.total_workers for stat in area_stats], 
             label='Area - Active', color='red', linewidth=2)
    ax2.plot(turns_a, [stat.replacement_workers for stat in area_stats], 
             label='Area - Reserve', color='red', linestyle='--')
    ax2.set_title('Worker Statistics')
    ax2.set_xlabel('Turns')
    ax2.set_ylabel('Workers')
    ax2.grid(True)
    ax2.legend()

    # Plot 3: Node Damage
    ax3.plot(turns_p, [stat.destroyed_nodes for stat in precision_stats], 
             label='Precision - Destroyed', color='blue', linewidth=2)
    ax3.plot(turns_p, [stat.damaged_nodes for stat in precision_stats], 
             label='Precision - Damaged', color='blue', linestyle='--')
    ax3.plot(turns_a, [stat.destroyed_nodes for stat in area_stats], 
             label='Area - Destroyed', color='red', linewidth=2)
    ax3.plot(turns_a, [stat.damaged_nodes for stat in area_stats], 
             label='Area - Damaged', color='red', linestyle='--')
    ax3.set_title('Node Damage')
    ax3.set_xlabel('Turns')
    ax3.set_ylabel('Count')
    ax3.grid(True)
    ax3.legend()

    # Plot 4: Edge Damage
    ax4.plot(turns_p, [stat.destroyed_edges for stat in precision_stats], 
             label='Precision - Destroyed', color='blue', linewidth=2)
    ax4.plot(turns_p, [stat.damaged_edges for stat in precision_stats], 
             label='Precision - Damaged', color='blue', linestyle='--')
    ax4.plot(turns_a, [stat.destroyed_edges for stat in area_stats], 
             label='Area - Destroyed', color='red', linewidth=2)
    ax4.plot(turns_a, [stat.damaged_edges for stat in area_stats], 
             label='Area - Damaged', color='red', linestyle='--')
    ax4.set_title('Edge Damage')
    ax4.set_xlabel('Turns')
    ax4.set_ylabel('Count')
    ax4.grid(True)
    ax4.legend()

    # Plot 5: Average Capacities
    ax5.plot(turns_p, [stat.avg_node_capacity for stat in precision_stats], 
             label='Precision - Node', color='blue', linewidth=2)
    ax5.plot(turns_p, [stat.avg_edge_capacity for stat in precision_stats], 
             label='Precision - Edge', color='blue', linestyle='--')
    ax5.plot(turns_a, [stat.avg_node_capacity for stat in area_stats], 
             label='Area - Node', color='red', linewidth=2)
    ax5.plot(turns_a, [stat.avg_edge_capacity for stat in area_stats], 
             label='Area - Edge', color='red', linestyle='--')
    ax5.set_title('Average Capacities')
    ax5.set_xlabel('Turns')
    ax5.set_ylabel('Capacity')
    ax5.grid(True)
    ax5.legend()

    # Plot 6: Workers Killed
    ax6.plot(turns_p, [stat.workers_killed for stat in precision_stats], 
             label='Precision', color='blue', linewidth=2)
    ax6.plot(turns_a, [stat.workers_killed for stat in area_stats], 
             label='Area', color='red', linewidth=2)
    ax6.set_title('Cumulative Worker Casualties')
    ax6.set_xlabel('Turns')
    ax6.set_ylabel('Workers Killed')
    ax6.grid(True)
    ax6.legend()

    plt.tight_layout()
    plt.savefig('detailed_bombing_analysis.png', dpi=300, bbox_inches='tight')

def print_final_statistics(precision_stats: List[SimulationStats], area_stats: List[SimulationStats]):
    """Print detailed final statistics"""
    p_final = precision_stats[-1]
    a_final = area_stats[-1]
    
    logging.debug("Printing final statistics.")
    print("\nFinal Statistics:")
    print("\nPrecision Bombing:")
    print(f"Turns to completion: {len(precision_stats)}")
    print(f"Final network output: {p_final.network_output:.2f}")
    print(f"Workers remaining: {p_final.total_workers:,} active, {p_final.replacement_workers:,} reserve")
    print(f"Infrastructure: {p_final.destroyed_nodes} nodes and {p_final.destroyed_edges} edges destroyed")
    print(f"Workers killed: {p_final.workers_killed:,}")
    print("\nEndpoint Outputs:")
    for endpoint, output in p_final.endpoint_outputs.items():
        print(f"Endpoint {endpoint}: {output:.2f}")
    
    print("\nArea Bombing:")
    print(f"Turns to completion: {len(area_stats)}")
    print(f"Final network output: {a_final.network_output:.2f}")
    print(f"Workers remaining: {a_final.total_workers:,} active, {a_final.replacement_workers:,} reserve")
    print(f"Infrastructure: {a_final.destroyed_nodes} nodes and {a_final.destroyed_edges} edges destroyed")
    print(f"Workers killed: {a_final.workers_killed:,}")
    print("\nEndpoint Outputs:")
    for endpoint, output in a_final.endpoint_outputs.items():
        print(f"Endpoint {endpoint}: {output:.2f}")

if __name__ == "__main__":
    # Simulation parameters
    num_nodes, num_edges = 1000, 4000
    workers_per_node = 10
    max_turns = 365  # One year of daily turns

    # Run simulations
    precision_stats = run_simulation(
        WarfareNetwork(num_nodes, num_edges, workers_per_node), 
        max_turns, 
        "precision"
    )
    
    area_stats = run_simulation(
        WarfareNetwork(num_nodes, num_edges, workers_per_node), 
        max_turns, 
        "area"
    )

    # Generate visualizations and statistics
    plot_detailed_results(precision_stats, area_stats)
    print_final_statistics(precision_stats, area_stats)

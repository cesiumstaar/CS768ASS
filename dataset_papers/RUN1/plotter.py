import pickle
import networkx as nx
import matplotlib.pyplot as plt
import sys

# --- Load graph ---
with open('citation_graph.pkl', 'rb') as f:
    G = pickle.load(f)

# --- Function to analyze and save ---
def analyze_graph(G, directed=True, title='', summary_filename='summary.txt'):
    with open(summary_filename, 'w', encoding='utf-8') as f:
        def print_log(*args, **kwargs):
            print(*args, **kwargs)
            print(*args, **kwargs, file=f)

        print_log(f"===== Analysis for {title} =====")

        # Number of edges
        print_log(f"Number of edges: {G.number_of_edges()}")

        # Number of isolated nodes
        isolated_nodes = list(nx.isolates(G))
        print_log(f"Number of isolated nodes: {len(isolated_nodes)}")

        # Average degrees
        if directed:
            avg_in_degree = sum(dict(G.in_degree()).values()) / G.number_of_nodes()
            avg_out_degree = sum(dict(G.out_degree()).values()) / G.number_of_nodes()
            print_log(f"Average In-Degree: {avg_in_degree:.2f}")
            print_log(f"Average Out-Degree: {avg_out_degree:.2f}")
        else:
            avg_degree = sum(dict(G.degree()).values()) / G.number_of_nodes()
            print_log(f"Average Degree: {avg_degree:.2f}")

        # Degree Histogram
        degrees = [d for n, d in G.degree()]
        plt.figure(figsize=(10,6))
        plt.hist(degrees, bins=30, color='skyblue', edgecolor='black')
        plt.title(f'Degree Distribution - {title}')
        plt.xlabel('Degree')
        plt.ylabel('Number of Nodes')
        plt.grid(True)

        # Save the plot
        filename = title.lower().replace(' ', '_') + '_degree_histogram.png'
        plt.savefig(filename, bbox_inches='tight')
        print_log(f"📸 Saved degree histogram to {filename}")
        plt.close()
        # Degree Histogram (zoomed-in version)
        degrees = [d for n, d in G.degree()]
        plt.figure(figsize=(10,6))
        plt.hist(degrees, bins=60, range=(0, 60), color='skyblue', edgecolor='black')
        plt.title(f'Degree Distribution (0-60) - {title}')
        plt.xlabel('Degree')
        plt.ylabel('Number of Nodes')
        plt.grid(True)

        # Save zoomed histogram
        filename_zoom = title.lower().replace(' ', '_') + '_degree_histogram_zoomed.png'
        plt.savefig(filename_zoom, bbox_inches='tight')
        print_log(f"📸 Saved zoomed degree histogram to {filename_zoom}")
        plt.close()


        # Components
        if directed:
            components = list(nx.weakly_connected_components(G))
            print_log(f"Number of weakly connected components: {len(components)}")
        else:
            components = list(nx.connected_components(G))
            print_log(f"Number of connected components: {len(components)}")

        component_sizes = [len(c) for c in components]
        for i, size in enumerate(component_sizes):
            print_log(f"Component {i+1}: {size} nodes")

        # Diameter analysis
        max_diameter = 0
        max_diameter_component_index = -1

        for idx, comp in enumerate(components):
            if len(comp) <= 1:
                continue
            subgraph = G.subgraph(comp)
            try:
                diameter = nx.diameter(subgraph)
                print_log(f"Diameter of component {idx+1} (size {len(comp)}): {diameter}")
                if diameter > max_diameter:
                    max_diameter = diameter
                    max_diameter_component_index = idx + 1
            except Exception as e:
                print_log(f"Failed to compute diameter for component {idx+1}: {e}")

        print_log(f"\n📏 Maximum diameter found: {max_diameter} (in component {max_diameter_component_index})")
        print_log("="*50)

# --- Run analysis on directed graph ---
analyze_graph(G, directed=True, title='Directed Citation Graph', summary_filename='summary_directed.txt')

# --- Convert to undirected ---
G_undirected = G.to_undirected()

# --- Run analysis on undirected graph ---
analyze_graph(G_undirected, directed=False, title='Undirected Citation Graph', summary_filename='summary_undirected.txt')

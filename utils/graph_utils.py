import pandas as pd
import networkx as nx
from community import community_louvain

def read_parquet_files():
    nodes_file = "output/20240719-222441/artifacts/create_final_nodes.parquet"
    relationships_file = "output/20240719-222441/artifacts/create_final_relationships.parquet"
    nodes_df = pd.read_parquet(nodes_file)
    relationships_df = pd.read_parquet(relationships_file)
    return nodes_df, relationships_df

def create_graph(nodes_df, relationships_df):
    graph = nx.Graph()
    node_id_col = 'id'
    node_label_col = 'title'
    source_id_col = 'source'
    target_id_col = 'target'
    edge_label_col = 'description'

    for _, row in nodes_df.iterrows():
        node_id = row[node_id_col]
        node_label = row.get(node_label_col, node_id)
        graph.add_node(node_id, label=node_label)

    for _, row in relationships_df.iterrows():
        graph.add_edge(row[source_id_col], row[target_id_col], label=row.get(edge_label_col, ''))

    return graph

def get_node_communities(graph):
    return community_louvain.best_partition(graph)

def get_node_centrality(graph, centrality_type='degree'):
    if centrality_type == 'degree':
        return nx.degree_centrality(graph)
    elif centrality_type == 'betweenness':
        return nx.betweenness_centrality(graph)
    elif centrality_type == 'closeness':
        return nx.closeness_centrality(graph)
    else:
        return nx.degree_centrality(graph)

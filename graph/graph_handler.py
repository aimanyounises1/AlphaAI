import networkx as nx
import pandas as pd

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

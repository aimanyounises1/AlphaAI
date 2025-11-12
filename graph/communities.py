from community import community_louvain

def get_node_communities(graph):
    return community_louvain.best_partition(graph)

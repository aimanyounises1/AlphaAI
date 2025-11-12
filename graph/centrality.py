import networkx as nx

def get_node_centrality(graph, centrality_type='degree'):
    if centrality_type == 'degree':
        return nx.degree_centrality(graph)
    elif centrality_type == 'betweenness':
        return nx.betweenness_centrality(graph)
    elif centrality_type == 'closeness':
        return nx.closeness_centrality(graph)
    else:
        return nx.degree_centrality(graph)

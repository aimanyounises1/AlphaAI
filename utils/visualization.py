import networkx as nx
import plotly.graph_objects as go
from community import community_louvain

def visualize_graph_plotly(graph, layout='spring', node_size_factor=10, edge_width=0.5,
                           color_by='community', centrality_type='degree', highlight_nodes=None):
    if layout == 'spring':
        pos = nx.spring_layout(graph, k=0.5, iterations=50)
    elif layout == 'circular':
        pos = nx.circular_layout(graph)
    elif layout == 'random':
        pos = nx.random_layout(graph)
    elif layout == 'shell':
        pos = nx.shell_layout(graph)
    else:
        pos = nx.spring_layout(graph, k=0.5, iterations=50)

    edge_x, edge_y = [], []
    for edge in graph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=edge_width, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x, node_y = [], []
    for node in graph.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    node_adjacencies = [len(list(graph.neighbors(node))) for node in graph.nodes()]
    node_text = [f'{graph.nodes[node].get("label", str(node))}<br># of connections: {adj}' for node, adj in zip(graph.nodes(), node_adjacencies)]

    if color_by == 'community':
        communities = community_louvain.best_partition(graph)
        node_colors = [communities[node] for node in graph.nodes()]
        colorscale = 'Viridis'
        colorbar_title = 'Community'
    elif color_by == 'centrality':
        if centrality_type == 'degree':
            centrality_values = nx.degree_centrality(graph)
        elif centrality_type == 'betweenness':
            centrality_values = nx.betweenness_centrality(graph)
        elif centrality_type == 'closeness':
            centrality_values = nx.closeness_centrality(graph)
        else:
            centrality_values = nx.degree_centrality(graph)
        node_colors = [centrality_values[node] for node in graph.nodes()]
        colorscale = 'YlOrRd'
        colorbar_title = f'{centrality_type.capitalize()} Centrality'
    else:
        node_colors = node_adjacencies
        colorscale = 'Viridis'
        colorbar_title = 'Degree'

    node_sizes = [max(10, min(50, adj * node_size_factor)) for adj in node_adjacencies]

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=node_text,
        textposition="top center",
        marker=dict(
            showscale=True,
            colorscale=colorscale,
            reversescale=True,
            color=node_colors,
            size=node_sizes,
            colorbar=dict(
                thickness=15,
                title=colorbar_title,
                xanchor='left',
                titleside='right'
            ),
            line_width=2))

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title='Interactive Graph Visualization',
                        titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        annotations=[dict(
                            text="",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.005, y=-0.002)],
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )

    fig.update_layout(clickmode='event+select')
    fig.update_layout(
        autosize=True,
        width=1000,
        height=800,
    )

    return fig, pos, graph

import pandas as pd

def read_parquet_files():
    nodes_file = "output/20240719-222441/artifacts/create_final_nodes.parquet"
    relationships_file = "output/20240719-222441/artifacts/create_final_relationships.parquet"
    nodes_df = pd.read_parquet(nodes_file)
    relationships_df = pd.read_parquet(relationships_file)
    return nodes_df, relationships_df

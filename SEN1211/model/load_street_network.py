import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import pickle

def load_street_network():
    data = pd.read_csv('coord_full.csv')

    pos = pd.read_csv('nodes_data.csv')
    
    G = nx.from_pandas_edgelist(data, source = "JointI", target = "JointJ", create_using=nx.Graph, edge_attr = True)

    positions = {}
    for n in G:
        row = pos[pos["node"] == n ]
        positions[n]= (float(row['x']),float(row['y']))
        
    nx.set_node_attributes(G,positions,"pos")

    #nx.draw_networkx(G, pos= positions, with_labels = False,node_size = 1 )

    with open('street_network.data', 'wb') as file:
        pickle.dump(G, file)
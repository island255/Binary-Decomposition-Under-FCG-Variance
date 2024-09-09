import networkx as nx

G = nx.DiGraph() # 创建有向图

G.add_edge(1, 2, weight=1)  # 添加 带权边，weight表示边权
G.add_edge(1, 3, weight=1)
G.add_edge(3, 1, weight=1)
G.add_edge(2, 4, weight=1)

print(G[1]) # 邻居的dict
print(list(G[1]))

print(G[2])

for nbr, value in G.adj[1].items(): # 枚举邻居
    print(nbr, value, value['weight'])
print('*' * 20)

for nbr, value in G[2].items(): # 枚举邻居，G[2]与G.adj[2]效果相同
    print(nbr, value, value['weight'])

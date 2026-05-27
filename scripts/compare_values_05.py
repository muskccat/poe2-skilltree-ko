import json

# Load GGG English 0.5
with open(r"D:\KS\자료들\_게임\POE2\data_ggg_05.json", encoding="utf-8") as f:
    d_ggg = json.load(f)

# Load Korean passiveskills from ggpk workspace
with open(r"D:\KS\자료들\_게임\POE2\ggpk_workspace\parsed\passiveskills_ko.json", encoding="utf-8") as f:
    ko_list = json.load(f)

# Load English passiveskills from ggpk workspace
with open(r"D:\KS\자료들\_게임\POE2\ggpk_workspace\parsed\passiveskills_en.json", encoding="utf-8") as f:
    en_list = json.load(f)

# Find "Mist Walk" or similar node. Let's find node by PassiveSkillGraphId
# Let's search for "안개" in ko_list
mist_nodes = [item for item in ko_list if '안개' in item.get('Name', '')]
print(f"Found {len(mist_nodes)} nodes with '안개' in parsed/passiveskills_ko.json")

for item in mist_nodes:
    graph_id = str(item.get("PassiveSkillGraphId"))
    ggg_node = d_ggg["nodes"].get(graph_id)
    en_item = next((x for x in en_list if x.get("PassiveSkillGraphId") == item.get("PassiveSkillGraphId")), None)
    
    print(f"\nGraphId: {graph_id}")
    print(f"  GGPK KO: Name: {item.get('Name')}, Stats: {item.get('Stats')}")
    print(f"           StatValues: {[item.get(f'Stat{i}Value') for i in range(1, 6)]}")
    if en_item:
        print(f"  GGPK EN: Name: {en_item.get('Name')}")
        print(f"           StatValues: {[en_item.get(f'Stat{i}Value') for i in range(1, 6)]}")
    if ggg_node:
        print(f"  GGG:     Name: {ggg_node.get('name')}, Stats: {ggg_node.get('stats')}")

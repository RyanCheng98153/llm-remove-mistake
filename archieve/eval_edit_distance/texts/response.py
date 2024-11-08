import sys, os, json
file = sys.argv[1]

with open (file, "r", encoding="utf-8") as f:
    texts = f.readlines()

count = 0
item_list = []

item = {"id": 0, "topic": "", "response": ""}

for line in texts:
    if line == "\n":
        continue
    
    if line.startswith(f"===[ {count} ]==="):
        if count != 0:
            item_list.append(item)
            item = {"id": count, "topic": "", "response": "" }
        count += 1
        continue
    
    if line.startswith("[topic]: "):
        topic = line[9: -1].lstrip()
        item["topic"] = topic
        continue
    
    item["response"] += line
item_list.append(item)

# Serializing json
json_object = json.dumps(item_list, indent=2)

fname, extension = os.path.splitext(file)
# Writing to sample.json
with open(f"{fname}.json", "w", encoding="utf-8") as outfile:
    outfile.write(json_object)
import os
import sys
import json

# Get the list of all files and directories
path = sys.argv[1]

dir_list = os.listdir(path)

if not os.path.exists(path):
    print("The path does not exist")
    sys.exit()

datasets = list()

for item in dir_list:
    with open(path + item) as f:
        datasets.append(json.load(f))

offset = 0

merge_json = []
for dataset in datasets:
    for data in dataset:
        data["id"] = offset
        offset += 1
    merge_json.extend(dataset)
    
    
with open("merged.json", "w") as f:
    json.dump(merge_json, f, indent=2)
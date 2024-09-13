import json

statelist = ['mistake', 'unrelevant', 'hestitate']
state = statelist[0]

dsfile = f"./datasets/dataset_{state}.json"

with open(dsfile, "r") as jsondata:
    dataset = json.load(jsondata)

print(dataset[0]['clean_article'])
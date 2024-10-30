import os
import sys
import json
from tqdm import tqdm

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

def lcs(s1, s2):
    n1 = len(s1)
    n2 = len(s2)

    dp = [[None] * (n2 + 1) for i in range(n1 + 1)]

    for i in range(n1 + 1):
        for j in range(n2 + 1):
            if i == 0 or j == 0 :
                dp[i][j] = 0
            elif s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
                
    return dp[n1-1][n2-1]

''' test
str1 = "This is a test"
str2 = "This is not a test"

print(lcs(str1.split(), str2.split()))
exit()
'''

results_article: dict[tuple[int, int], list[int]] = {}
results_answer: dict[tuple[int, int], list[int]] = {}


for i in range(0, 1):
    for j in range(i, len(datasets)):
        if j == i:
            continue
        results_article[(i, j)] = []
        results_answer[(i, j)] = []
        
for i in range(0, 1):
    for j in range(i, len(datasets)):
        if j == i:
            continue
        
        file_i = dir_list[i].split("(")[1].split(")")[0]
        file_j = dir_list[j].split("(")[1].split(")")[0]
        
        print("Comparing dataset " + file_i + " with dataset " + file_j)
        
        for data in tqdm(datasets[i]):
            article = data['article'].split()
            answer = data['answer'].split()
            
            # check the maximum lcs between the article and the articles in the other dataset
            max_article_lcs = max( [lcs( article, data2['article'].split() ) for data2 in datasets[j]] )
            max_answer_lcs = max( [lcs( answer, data2['answer'].split() ) for data2 in datasets[j]] )
            
            # calculate the similarity of the article and the answer
            results_article[(i, j)].append( max_article_lcs / len(article) )
            results_answer[(i, j)].append( max_answer_lcs / len(answer) ) 

            # check for duplicates
            for data2 in datasets[j]:
                article2 = data2['article']
                answer2 = data2['answer']
                
                if article == article2:
                    print("Duplicate article found")
                    sys.exit()
                
                if answer == answer2:
                    print("Duplicate answer found")
                    sys.exit()
                    
        file_i = dir_list[i].split("(")[1].split(")")[0]
        file_j = dir_list[j].split("(")[1].split(")")[0]
        
        print(f"Article similarity, dataset({file_i}, {file_j}): { max( results_article[(i, j)] ) }")
        print(f"Answer similarity, dataset({file_i}, {file_j}): { max( results_answer[(i, j)] ) }")
        
for i in range(0, 1):
    for j in range(i, len(datasets)):
        if j == i:
            continue
        
        file_i = dir_list[i].split("(")[1].split(")")[0]
        file_j = dir_list[j].split("(")[1].split(")")[0]
        
        print(f"Article similarity, dataset({file_i}, {file_j}): { max( results_article[(i, j)] ) }")
        print(f"Answer similarity, dataset({file_i}, {file_j}): { max( results_answer[(i, j)] ) }")
        
import sys
import json

def getRaw(filename: str):
    rawdata = []
    
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
        for i in range(len(lines)):
            if( lines[i].startswith("===")):
                x = int(lines[i].lstrip("===[").rstrip("]===\n"))
                
                i+=1
                article = ""
                while( i < len(lines)-1 and not lines[i+1].startswith("===") ):
                    article += lines[i]
                    i+=1
                
                title_end = article.find("\n")
                title = article[:title_end]
                topic_start = title.find("Topic:")
                topic = title[topic_start+7 : title_end-1]
                article = article[title_end+2:-1]
                
                data = {"id": x, "topic": topic, "marked_article": article }
                rawdata.append(data)
    return rawdata

import re
def split_marked_article(marked_article, id):
    print(id)
    """將marked_article拆分成mistake部分、hint部分、和正常部分"""
    mistake_pattern = re.compile(r"<m>(.*?)</m>")
    hint_pattern = re.compile(r"<hint>(.*?)</hint>")

    mistakes = mistake_pattern.findall(marked_article)
    hints = hint_pattern.findall(marked_article)
    
    # Use regular expressions to remove the <m>, </m>, <hint>, and </hint> tags
    clean_article = re.sub(r'</?m>|</?hint>', '', marked_article)
    
    # 移除mistake和hint標記來提取正常的文章部分
    answer = re.sub(mistake_pattern, "", marked_article)
    answer = re.sub(hint_pattern, "", answer).strip()
    
    return mistakes[0], hints[0], clean_article, answer

def getDataset(rawdata: list[dict]):
    for i in range(0, len(rawdata)):
        mistake, hint, article, answer = split_marked_article(rawdata[i]['marked_article'], rawdata[i]['id'])
        rawdata[i]['mistake'] = mistake
        rawdata[i]['hint'] = hint
        rawdata[i]['article'] = article
        rawdata[i]['answer'] = answer
        
        # Desired order of keys
        desired_order = ['id', 'topic', 'article', 'answer', 'mistake', 'hint', 'marked_article']
        # Reorder by custom order
        rawdata[i] = {key: rawdata[i][key] for key in desired_order}
    return rawdata

def sortDataset(dataset):
    short_articles = []
    long_articles = []
    
    for data in dataset:
        marked_article = data.get('marked_article', '')
        article = data.get('article', '')

        # Check if both 'marked_article' or 'article' have more than 170 words
        if len(marked_article.split()) > 170 or len(article.split()) > 170:
            long_articles.append(data)  # Add to long articles list
        else:
            short_articles.append(data)  # Add to short articles list

    # Return a list with short articles followed by long articles
    sortedDataset = short_articles + long_articles
    for i in range(0, len(sortedDataset)):
        sortedDataset[i]["id"] = i
    return sortedDataset

import os
def uniquify(path:str)->str:
    filename, extension = os.path.splitext(path)
    counter = 1
    while os.path.exists(path):
        originPath = path
        path = filename + "(" + str(counter) + ")" + extension
        counter += 1
    if counter != 1:
        pass
        print(f"{originPath} has existed. --> {path} is now created.")
    return path

def main():
    infile = sys.argv[1]
    state = infile[infile.find("_")+1 : infile.find(".md")]
    raw = getRaw(infile)
    dataset = getDataset(raw[:])
    sortedDatasets = sortDataset(dataset)
    
    json_object = json.dumps(sortedDatasets, indent=2)

    filename = f"./datasets/{state[:state.find('(')]}/dataset_{state}.json"
    with open (uniquify(filename), "w") as f:
        f.write(json_object)
    
if __name__ == "__main__":
    main()
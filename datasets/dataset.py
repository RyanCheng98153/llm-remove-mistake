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
                
                data = {"id": x, "topic": topic, "article": article }
                rawdata.append(data)
    return rawdata

def getDataInfo(article: str):
    m_start = article.find("<m>") 
    m_end = article.find("</m>")
    mistake = article[m_start + 4 : m_end]
    
    hint_start = article.find("<hint>")
    hint_end = article.find("</hint>")
    hint = article[hint_start + 7 : hint_end]
    
    clean_article = article
    for item in ["<hint>", "</hint>", "<m>", "</m>", "<hestitate>", "</hestitate>", "<unrelevant>", "</unrelevant>"]:
        clean_article = clean_article.replace(item, "")
    answer = article[:m_start] + article[m_end + 5 : hint_start] + article[hint_end + 9:-1]
    
    return mistake, hint, clean_article, answer 
    
def getDataset(rawdata: list[dict]):
    for data in rawdata:
        mistake, hint, clean_article, answer = getDataInfo(data['article'])
        data['mistake'] = mistake
        data['hint'] = hint
        data['clean_article'] = clean_article
        data['answer'] = answer
        
    return rawdata
    
def main():
    infile = sys.argv[1]
    state = infile[infile.find("_")+1 : infile.find(".md")]
    dataset = getDataset(getRaw(infile))
    
    json_object = json.dumps(dataset, indent=2)

    with open (f"./datasets/dataset_{state}.json", "w") as f:
        f.write(json_object)
    
if __name__ == "__main__":
    main()
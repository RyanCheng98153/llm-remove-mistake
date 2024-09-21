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

def getDataInfo(marked_article: str, id):
    print(id)
    article = marked_article
    answer = marked_article
    mistake = []
    hint = []
    
    while("<m>" in answer and "</m>" in answer and "<hint>" in answer and "</hint>" in answer):
        m_start = answer.find("<m>")
        m_end = answer.find("</m>")
        mistake.append(answer[m_start + 4 : m_end])
        
        hint_start = answer.find("<hint>")
        hint_end = answer.find("</hint>")
        hint.append(answer[hint_start + 7 : hint_end])
        
        answer = answer[:m_start] + answer[m_end + 5 : hint_start] + answer[hint_end + 9:-1]
        
    for item in ['<m>', "</m>", "<hint>", "</hint>"]:
        article = article.replace(item, "")
        
    return mistake[0], hint[0], article, answer 
    
def getDataset(rawdata: list[dict]):
    for i in range(0, len(rawdata)):
        mistake, hint, article, answer = getDataInfo(rawdata[i]['marked_article'], rawdata[i]['id'])
        rawdata[i]['mistake'] = mistake
        rawdata[i]['hint'] = hint
        rawdata[i]['article'] = article
        rawdata[i]['answer'] = answer
        
        # Desired order of keys
        desired_order = ['id', 'topic', 'article', 'answer', 'mistake', 'hint', 'marked_article']
        # Reorder by custom order
        rawdata[i] = {key: rawdata[i][key] for key in desired_order}
    return rawdata
    
def main():
    infile = sys.argv[1]
    state = infile[infile.find("_")+1 : infile.find(".md")]
    raw = getRaw(infile)
    dataset = getDataset(raw[:])
    
    json_object = json.dumps(dataset, indent=2)

    with open (f"../datasets/dataset_{state}.json", "w") as f:
        f.write(json_object)
    
if __name__ == "__main__":
    main()
import json
import torch
import time
import sys

def getDataset(i):
    statelist = ['mistake', 'mistake_short', 'unrelevant', 'hestitate']
    state = statelist[1]

    dsfile = f"./datasets/{state}/dataset_{state}({i}).json"
    # dsfile = f"./datasets/{state}/dataset_{state}(2).json"

    with open(dsfile, "r") as jsondata:
        dataset = json.load(jsondata)
    return dataset


# === start eval
import difflib

def evaluate_response(response, test_data):
    article = test_data['article']
    answer = test_data['answer']
    mistake = test_data['mistake']
    hint = test_data['hint']
    
    # Compute the differences
    diff = list(difflib.ndiff(article, response))
    """ check the differenece of article and sequence,
        + for generated new content by target
        - for removing content by target compare with article. removing part == mistake and hint  
    """
    
    # print(diff)
    remove_part = [d[2: ] for d in diff if d[0] == '-']
    add_part  = [d[2: ] for d in diff if d[0] == '+']

    mishint_diff = list(difflib.ndiff(mishint, remove_part))
    # print(remove_part)
    # print(mishint_diff)
    
    stopwords = ['the', 'The']
    retain_mishint  = [d[2: ] for d in mishint_diff if d[0] == '-' and d[2:] not in stopwords]
    over_remove     = [d[2: ] for d in mishint_diff if d[0] == '+' and d[2:] not in stopwords]

    retain_mishint_score = len(retain_mishint) / len(mishint) * 100
    over_remove_score = len(over_remove) / len(answer) * 100
    add_part_score = len(add_part) / len(answer) * 100
    
    retain_mishint_score_text = f"score retain_mishint:\t {round(retain_mishint_score, 3)} %, ( {len(retain_mishint)} / {len(mishint)} )"
    over_remove_score_text =    f"score over_remove:   \t {round(over_remove_score, 3)} %, ( {len(over_remove)} / {len(answer)} )"
    add_part_score_text =       f"score add_content:   \t {round(add_part_score, 3)} %, ( {len(add_part)} / {len(answer)} )"
    
    return {
        "retain_mishint": retain_mishint,
        "over_remove": over_remove,
        "add content": add_part,
        "retain_mishint_score": retain_mishint_score, 
        "over_remove_score": over_remove_score, 
        "add_part_score": add_part_score,
        "retain_mishint_score_text": retain_mishint_score_text, 
        "over_remove_score_text": over_remove_score_text, 
        "add_part_score_text": add_part_score_text
    }

# === end eval

def main():
    # instruction = "In the article, help me eliminate the only mistake sentences and only hint sentences that indicates the mistake sentences. "
    instruction = "In the article, help me eliminate the only mistake sentences that introduces a factual error and the corresponding hint sentences clarifies that error by directly addressing the information provided in the mistake sentence."
    # instruction = "In the article provided below. Eliminate the only mistake sentences from the article along with the hint sentences, and keep only the correct ones."
    # instruction = "Find the only mistake sentences and the corresponding hint sentences in the article. The mistake sentence introduces a factual error, while the hint sentence clarifies or corrects that error by directly addressing the information provided in the mistake sentence."
    
    correct = 0
    wrong = 0
    complete_correct = 0
    
    filename = sys.argv[1]
    
    total_score = {
        "retain_mishint_score": 0, 
        "over_remove_score": 0, 
        "add_part_score": 0,
    }
    
    # Opening JSON file
    with open(filename) as json_file:
        resdata = json.load(json_file)
    
    ds_i = int(sys.argv[2])
    dataset = getDataset(ds_i)
    for iter in range(0, len(dataset)):
    # for iter in range(0, 1):
        print(iter)
        print(len(dataset))
        data = dataset[iter]
        
        # print(data)
        
        # article = data['marked_article']
        article = data['article']
        prompt = instruction + "\nArticle:\n" + article
        # prompt = "Where is the capital city of France."
        
        # response = getResponse(prompt, max_new_tokens=250)
        
        prompt = article
        response = resdata[iter]['response']
        
        
        printText = f"===[ {data['id']} ]===" + "\n"
        printText += f"[topic]: {data['topic']}" + "\n\n"
        
        """ for checking
        printText += "[response / answer / marked_article / mishint]\n"
        printText += response
        printText += answer + "\n"
        printText += data['marked_article'] + "\n"
        printText += (mistake+hint).lstrip()
        printText += "\n\n"
        """
        
        evaluation = evaluate_response(response, data)
        
        printText += "[Evaluation]:\n"
        for k in evaluation.keys():
            if k.endswith("score"):
                continue
            if k.endswith("text"):
                printText += f"{evaluation[k]}\n"
            else:
                printText += f"{k}:\t{evaluation[k]}\n"

        printText += "\n"
        total_score["retain_mishint_score"] += evaluation["retain_mishint_score"] 
        total_score["over_remove_score"] += evaluation["over_remove_score"] 
        total_score["add_part_score"] += evaluation["add_part_score"] 
        
        avg_retain_mishint_score =  round(total_score["retain_mishint_score"] / ( iter+1 ), 3) 
        avg_over_remove_score =     round(total_score["over_remove_score"] / ( iter+1 ), 3) 
        avg_add_part_score =        round(total_score["add_part_score"] / ( iter+1 ), 3) 
        
        printText += "[Average score]:\n"
        printText += (f"avg: retain_mishint:\t{avg_retain_mishint_score} %, \n" +
                      f"avg: over_remove:\t\t{avg_over_remove_score} %, \n" +
                      f"avg: add_content:\t\t{avg_add_part_score} %\n")
        
        
        printText += "\n"
        if evaluation["retain_mishint_score"] < 6 and evaluation["add_part_score"] < 4:
            correct += 1
            
            if (evaluation["retain_mishint_score"] < 1 and evaluation["add_part_score"] < 1.6 and evaluation["over_remove_score"] < 1.6 ):
                complete_correct += 1
                printText += f"[ Complete Correct ]\n"
            else:
                printText += f"[ Correct ]\n"
        else:
            wrong += 1
            printText += f"[ Wrong ]\n"
        
        printText += (f"[Total: {iter+1}, Correct: {correct}, Wrong: {wrong}, Complete_Correct: {complete_correct}]\n")
        
        printText += "\n"
        
        if "removellm" in filename:
            filename = f"eval_removellm({ds_i}).txt"
        if "smollm" in filename:
            filename = f"eval_smollm({ds_i}).txt"
        
        with open("eval/responses/" + filename, "a", encoding="utf-8") as f:
            f.writelines(printText)
        
if __name__ == "__main__":
    main()
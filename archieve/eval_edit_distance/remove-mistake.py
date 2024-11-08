import json
import torch
import time
import sys
# Load model directly
from transformers import AutoTokenizer, AutoModelForCausalLM, PreTrainedModel

device = "cpu" # "cuda" for GPU usage or "cpu" for CPU usage
smollm_checkpoint = "HuggingFaceTB/SmolLM-360M-Instruct"
# checkpoint = "ryan98153/SmolLM-135M-fine-tuned2"
checkpoint = sys.argv[1]
# checkpoint = "HuggingFaceTB/SmolLM-1.7B-Instruct"
# for multiple GPUs install accelerate and do `model = AutoModelForCausalLM.from_pretrained(checkpoint, device_map="auto")`
tokenizer = AutoTokenizer.from_pretrained(smollm_checkpoint, cache_dir="./.cache")
model: PreTrainedModel = AutoModelForCausalLM.from_pretrained(checkpoint, cache_dir="./.cache").to(device)

def calculate_time(func):
    def inner1(*args, **kwargs):
        begin = time.time()
        returned_value = func(*args, **kwargs)
        end = time.time()
        
        print("Take time:", end - begin, "seconds\n")
        return returned_value

    return inner1

def getDataset(i):
    statelist = ['mistake', 'mistake_short', 'unrelevant', 'hestitate']
    state = statelist[1]

    dsfile = f"./datasets/{state}/dataset_{state}({i}).json"
    # dsfile = f"./datasets/{state}/dataset_{state}(2).json"

    with open(dsfile, "r") as jsondata:
        dataset = json.load(jsondata)
    return dataset

@calculate_time
def getResponse(prompt: str, max_new_tokens: int = 50):
    messages = [{"role": "user", "content": prompt}]

    input_text=tokenizer.apply_chat_template(messages, tokenize=False)
    # print(input_text)
    input_ids = tokenizer.encode(input_text, return_tensors="pt").to(device)
    attention_mask = torch.ones(input_ids.shape,dtype=torch.long,device=device)
    outputs = model.generate(
        input_ids, 
        max_new_tokens=max_new_tokens, 
        # max_length=max_new_tokens,
        attention_mask=attention_mask,
        pad_token_id=tokenizer.eos_token_id,
        temperature=0.2, 
        top_p=0.9, 
        do_sample=True
        )
    response = tokenizer.decode(outputs[0])
    
    start = response.find("<|im_start|>assistant")
    if response !=-1:
        response = response[start + 21:]
    
    return response

def getFinetunedResponse(prompt: str, max_new_tokens: int = 50):
    input_ids = tokenizer.encode(prompt, return_tensors="pt", add_special_tokens=False).to(device)
    # inputs = tokenizer.encode(prompt).to(device)

    attention_mask = torch.ones(input_ids.shape,dtype=torch.long,device=device)
    
    generated_ids = model.generate(
    inputs=input_ids,
    max_new_tokens=max_new_tokens,
    attention_mask=attention_mask,
    pad_token_id=tokenizer.eos_token_id,
    eos_token_id=tokenizer.eos_token_id,
    )

    generated_text = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
    generated_text = generated_text.replace(prompt, "").strip()

    return generated_text

# === start eval
import difflib

def evaluate_response(response, test_data):
    article = test_data['article']
    answer = test_data['answer']
    mistake = test_data['mistake']
    hint = test_data['hint']
    
    response = response.split()
    article = article.split()
    answer = answer.split()
    mishint = ( mistake + hint ).split()
    
    # Compute the differences
    diff = list(difflib.ndiff(article, response))
    """ check the differenece of article and sequence,
        + for generated new content by target
        - for removing content by target compare with article. removing part == mistake and hint  
    """
    
    remove_part = [d[2: ] for d in diff if d[0] == '-']
    add_part  = [d[2: ] for d in diff if d[0] == '+']

    mishint_diff = list(difflib.ndiff(mishint, remove_part))
    
    stopwords = ['the', 'The']
    retain_mishint  = [d[2: ] for d in mishint_diff if d[0] == '-' and d[2:] not in stopwords]
    over_remove     = [d[2: ] for d in mishint_diff if d[0] == '+' and d[2:] not in stopwords]

    retain_mishint_score = len(retain_mishint) / len(mishint) * 100
    over_remove_score = len(over_remove) / len(answer) * 100
    add_part_score = len(add_part) / len(answer) * 100
    
    retain_mishint_score_text = f"score retain_mishint:\t {len(retain_mishint)} / {len(mishint)}: {round(retain_mishint_score, 3)} %"
    over_remove_score_text =    f"score over_remove:\t {len(over_remove)} / {len(answer)}: {round(over_remove_score, 3)} %"
    add_part_score_text =       f"score add_content:\t {len(add_part)} / {len(answer)}: {round(add_part_score, 3)} %"
    
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

import time

def main():
    # instruction = "In the article, help me eliminate the only mistake sentences and only hint sentences that indicates the mistake sentences. "
    instruction = "In the article, help me eliminate the only mistake sentences that introduces a factual error and the corresponding hint sentences clarifies that error by directly addressing the information provided in the mistake sentence."
    # instruction = "In the article provided below. Eliminate the only mistake sentences from the article along with the hint sentences, and keep only the correct ones."
    # instruction = "Find the only mistake sentences and the corresponding hint sentences in the article. The mistake sentence introduces a factual error, while the hint sentence clarifies or corrects that error by directly addressing the information provided in the mistake sentence."
    
    correct = 0
    wrong = 0
    complete_correct = 0
    
    total_score = {
        "retain_mishint_score": 0, 
        "over_remove_score": 0, 
        "add_part_score": 0,
    }
    
    ds_i = int(sys.argv[2])
    dataset = getDataset(ds_i)
    
    start = 0
    
    if len(sys.argv) > 3: 
        start = int(sys.argv[3])
    
    for iter in range(start, len(dataset)):
    # for iter in range(0, 1):
        data = dataset[iter]
        
        # print(data)
        
        # article = data['marked_article']
        article = data['article']
        prompt = instruction + "\nArticle:\n" + article
        # prompt = "Where is the capital city of France."
        
        # response = getResponse(prompt, max_new_tokens=250)
        
        prompt = article
        
        if checkpoint.startswith("HuggingFaceTB/"):
            response = getResponse(prompt, max_new_tokens=250)
        if checkpoint.startswith("ryan98153/"):
            response = getFinetunedResponse(prompt, max_new_tokens=250)
        
        
        printText = f"===[ {data['id']} ]===" + "\n"
        printText += f"[topic]: {data['topic']}" + "\n\n"
        
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
        
        if checkpoint == "ryan98153/SmolLM-135M-fine-tuned2":
            filename = f"./eval/responses/eval_removellm({ds_i}).md"
            textfilename = f"./eval/texts/text_removellm({ds_i}).md"
        elif checkpoint == "HuggingFaceTB/SmolLM-360M-Instruct":
            filename = f"./eval/responses/eval_smollm({ds_i}).md"
            textfilename = f"./eval/texts/text_smollm({ds_i}).md"
        with open(filename, "a", encoding="utf-8") as f:
            f.writelines(printText)
        with open(textfilename, "a", encoding="utf-8") as f:
            printText2 = f"===[ {data['id']} ]===" + "\n"
            printText2 += f"[topic]: {data['topic']}" + "\n\n"
            f.writelines(printText2 + response +"\n")
        
            
if __name__ == "__main__":
    main()
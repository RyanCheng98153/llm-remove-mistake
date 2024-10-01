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
# checkpoint = "microsoft/Phi-3-mini-4k-instruct"
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
    
    print(response)
    start = response.find("<|im_start|>assistant")
    if response !=-1:
        response = response[start + 21:]
    
    return response

def getFinetunedResponse(prompt: str, max_new_tokens: int = 50):
    # prompt = "Small models are great.\n"
    #Small models are great.
    #{"Small": "models", "are": "great"}
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

import re
from rouge_score import rouge_scorer

def split_into_sentences(text):
    # Regular expression pattern, based on periods, question marks, and exclamation marks
    sentence_endings = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s'
    return re.split(sentence_endings, text)    
    
# Function to calculate ROUGE-L score using rouge-score library
def cal_rougeL(reference, hypothesis):
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = scorer.score(reference, hypothesis)
    return scores['rougeL'].fmeasure  # Return only the f1-measure of ROUGE-L

def cal_split_rougeL(reference, hypothesis):
    split_reference = split_into_sentences(reference)
    max_rougeL = 0
    
    for split_ref in split_reference:
        split_rougeL = cal_rougeL(split_ref, hypothesis)
        if max_rougeL < split_rougeL:
            max_rougeL = split_rougeL
    return max_rougeL  # Return the max f1-measure of ROUGE-L

def evaluate_response(response, answer, mistake, hint, 
                      threshold_clean =  0.9, 
                      threshold_mistake = 0.75, 
                      threshold_hint = 0.75):
    # Compute ROUGE-L scores
    clean_retained_score =      round(cal_rougeL(answer,    response), 2)
    mistake_presence_score =    round(cal_rougeL(mistake,   response), 2)
    hint_presence_score =       round(cal_rougeL(hint,      response), 2)
    
    split_response =  split_into_sentences(response)
    
    # Compute ROUGE-L scores of every sentence with answer, mistake, hint content
    response_rougeL = [{"clean":    round(cal_split_rougeL(answer,    sent), 2),
                        "mistake":  round(cal_split_rougeL(mistake,   sent), 2),
                        "hint":     round(cal_split_rougeL(hint,      sent), 2),
                        "sent": sent 
                        } for sent in split_response]
    
    # Filter out related/unrelated content based on sentence-wise ROUGE-L score
    clean_retained_sentences =      [obj['sent'] for obj in response_rougeL if obj['clean']     >= threshold_clean]
    mistake_sentences_in_response = [obj['sent'] for obj in response_rougeL if obj['mistake']   >= threshold_mistake]
    hint_sentences_in_response =    [obj['sent'] for obj in response_rougeL if obj['hint']      >= threshold_hint]
    
    # Unrelated sentences: those not found in any of the previous categories
    unrelated_sentences = [sent for sent in split_response if (
        sent not in clean_retained_sentences and
        sent not in mistake_sentences_in_response and
        sent not in hint_sentences_in_response
    )]
    
    # Final score (weighted sum of normalized scores)
    # final_score = (0.5 * clean_retained_score + 
    #                0.25 * mistake_removed_score + 
    #                0.25 * hint_removed_score)
    final_score = 0
    
    result = {
        "clean_retained_score": clean_retained_score,
        "mistake_presence_score": mistake_presence_score,
        "hint_presence_score": hint_presence_score,
        "final_score": final_score,
        "answer": {answer},
        "clean_content_retained": clean_retained_sentences,
        # "clean": f"{len(clean_retained_sentences)} / {len(clean_retained_sentences)}",
        "mistake": {mistake},
        "mistake_content_in_response": mistake_sentences_in_response,
        # "mistake": f"{len(mistake_sentences_in_response)} / {len(mistake_sentences_in_response)}",
        "hint": {hint},
        "hint_content_in_response": hint_sentences_in_response,
        # "hint": f"{len(hint_sentences_in_response)} / {len(hint_sentences_in_response)}",
        # "unrelated_content_in_response": unrelated_sentences,
        "unrelated_num": len(unrelated_sentences),
        "response_rougeL": response_rougeL,
    }

    return result

# === end eval

import time

def main():
    # instruction = "In the article, help me eliminate the only mistake sentences and only hint sentences that indicates the mistake sentences. "
    instruction = "In the article, help me eliminate the only mistake sentences that introduces a factual error and the corresponding hint sentences clarifies that error by directly addressing the information provided in the mistake sentence."
    # instruction = "In the article provided below. Eliminate the only mistake sentences from the article along with the hint sentences, and keep only the correct ones."
    # instruction = "Find the only mistake sentences and the corresponding hint sentences in the article. The mistake sentence introduces a factual error, while the hint sentence clarifies or corrects that error by directly addressing the information provided in the mistake sentence."
    
    correct = 0
    wrong = 0
    
    threshold_clean =  0.9
    threshold_mistake = 0.75 
    threshold_hint = 0.75
    
    Average_clean = 0.0
    Average_mistake = 0.0
    Average_hint = 0.0
    
    Average_sent_clean = 0.0
    Average_sent_mistake = 0.0
    Average_sent_hint = 0.0
    
    ds_i = int(sys.argv[2])
    dataset = getDataset(ds_i)
    for iter in range(0, len(dataset)):
    # for iter in range(0, 1):
        data = dataset[iter]
        
        # print(data)
        
        # article = data['marked_article']
        article = data['article']
        prompt = instruction + "\nArticle:\n" + article
        # prompt = "Where is the capital city of France."
        
        # response = getResponse(prompt, max_new_tokens=250)
        
        prompt = article
        response = getFinetunedResponse(prompt, max_new_tokens=250)
        # print(response)
        
        answer = data['answer']
        mistake = data['mistake']
        hint = data['hint']
        
        evaluation = evaluate_response(response, answer, mistake, hint,
                                       threshold_clean,
                                       threshold_mistake,
                                       threshold_hint
                                       )
        
        printText = f"===[ {data['id']} ]===" + "\n"
        printText += f"[topic]: {data['topic']}" + "\n\n"
        
        # printText += f"[marked_article]: \n{data['marked_article']}" + "\n\n"
        """
        printText += f"[prompt]:\n"
        printText += f"{prompt}" + "\n\n"
        
        printText += f"[response]:\n"
        printText += f"{response}" + "\n\n"
        """
        
        printText += f"[eval]:" + "\n"
        for k in evaluation.keys():
            """
            if k == "answer":
                printText += (f"{k}: {evaluation[k]}") + "\n\n"
                
                continue
            """
            if k in ["clean_retained_score", "mistake_presence_score", "hint_presence_score"]:
                printText += (f"{k}: {evaluation[k]}") + "\n"
                continue
            if k == "unrelated_num":
                printText += (f"{k}: {evaluation[k]} / {len(response)}") + "\n"
                lenResponse = len(split_into_sentences(response))
                continue
            if k == "response_rougeL":
                printText += "\n" + "[rougeL]:"+ "\n"
                
                lenResponse = len(split_into_sentences(response))
                lenClean = len([obj for obj in evaluation[k] if(obj['clean'] > threshold_clean)])
                lenMistake = len([obj for obj in evaluation[k] if(obj['mistake'] > threshold_mistake)])
                lenHint = len([obj for obj in evaluation[k] if(obj['hint'] > threshold_hint)])
                
                lenOriginClean   = len(split_into_sentences(data['answer']))
                lenOriginMistake = len(split_into_sentences(data['mistake']))
                lenOriginHint    = len(split_into_sentences(data['hint']))
                
                if lenResponse == lenClean and lenMistake == 0 and lenHint == 0:
                    correct += 1
                    if lenClean == lenOriginClean and evaluation['unrelated_num'] == 0:
                        printText += "[Complete Right]\n"
                    else:
                        printText += "[Right]\n"
                else:
                    wrong += 1
                    printText += "[Wrong]\n"
                print(f"[Total: {correct + wrong}, Correct: {correct}, Wrong: {wrong}]: LenResponse: {lenResponse}, clean {lenClean} / {lenOriginClean}, mistake {lenMistake} / {lenOriginMistake}, hint {lenHint} / {lenOriginHint}")
                
                printText += f"LenResponse: {lenResponse}, clean {lenClean} / {lenOriginClean}, mistake {lenMistake} / {lenOriginMistake}, hint {lenHint} / {lenOriginHint}" + "\n\n"
                avgClean = 0.0
                avgMistake = 0.0
                avgHint = 0.0
                for obj in evaluation[k]:
                    printText += (f"clean: {obj['clean']}\t, mistake: {obj['mistake']}, \t hint: {obj['hint']}\t \n\t{obj['sent']}") + "\n"
                    
                    avgClean += obj['clean']
                    avgMistake += obj['mistake']
                    avgHint += obj['hint']
                # Calculate the average of clean, mistake, hint content
                avgClean = round(avgClean / len(evaluation[k]), 3)
                avgMistake = round(avgMistake / len(evaluation[k]), 3)
                avgHint = round(avgHint / len(evaluation[k]), 3)
                print(f"[Average] clean: {avgClean},\tmistake: {avgMistake},\thint: {avgHint}\t")
                printText += f"[Average] clean: {avgClean},\tmistake: {avgMistake},\thint: {avgHint}" + "\n"
                
                Average_sent_clean += avgClean
                Average_sent_mistake += avgMistake
                Average_sent_hint += avgHint
                
                Average_clean += evaluation["clean_retained_score"]
                Average_mistake += evaluation["mistake_presence_score"]
                Average_hint += evaluation["hint_presence_score"]
                
                continue
            
            # printText += (f"{k}: {evaluation[k]}") + "\n"
            
        printText += "\n"
        printText += (f"[Total: {correct + wrong}, Correct: {correct}, Wrong: {wrong}]\n")
        printText += (f"[Total Sent Average]: clean: {round(Average_sent_clean / (iter+1), 4)},\tmistake: {round(Average_sent_mistake / (iter+1), 4)},\thint: {round(Average_sent_hint / (iter+1), 4)}" + "\n")
        printText += (f"[Total Average]: clean: {round(Average_clean / (iter+1), 4)},\tmistake: {round(Average_mistake / (iter+1), 4)},\thint: {round(Average_hint / (iter+1), 4)}" + "\n")
        printText += "\n"
        
        if checkpoint == "ryan98153/SmolLM-135M-fine-tuned2":
            filename = f"./eval/responses/eval_removellm({ds_i}).md"
        elif checkpoint == "HuggingFaceTB/SmolLM-360M-Instruct":
            filename = f"./eval/responses/eval_smollm({ds_i}).md"
        with open(filename, "a", encoding="utf-8") as f:
            f.writelines(printText)
            
if __name__ == "__main__":
    main()
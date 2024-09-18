import json
import torch
import time
# Load model directly
from transformers import AutoTokenizer, AutoModelForCausalLM

device = "cpu" # "cuda" for GPU usage or "cpu" for CPU usage
checkpoint = "HuggingFaceTB/SmolLM-360M-Instruct"
# checkpoint = "HuggingFaceTB/SmolLM-1.7B-Instruct"
# checkpoint = "microsoft/Phi-3-mini-4k-instruct"
# for multiple GPUs install accelerate and do `model = AutoModelForCausalLM.from_pretrained(checkpoint, device_map="auto")`
tokenizer = AutoTokenizer.from_pretrained(checkpoint, cache_dir="./.cache")
model = AutoModelForCausalLM.from_pretrained(checkpoint, cache_dir="./.cache").to(device)

def calculate_time(func):
    def inner1(*args, **kwargs):
        begin = time.time()
        returned_value = func(*args, **kwargs)
        end = time.time()
        
        print("Take time:", end - begin, "seconds\n")
        return returned_value

    return inner1

def getDataset():
    statelist = ['mistake', 'mistake_short', 'unrelevant', 'hestitate']
    state = statelist[1]

    dsfile = f"./datasets/dataset_{state}.json"

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
    return tokenizer.decode(outputs[0])

def main():
    # instruction = "In the article, help me eliminate the only mistake sentences and only hint sentences that indicates the mistake sentences. "
    # instruction = "In the article, identify the mistake sentence containing factual error and provide the hint sentence that points to this mistake."
    # instruction =  "Find the only mistake sentences and hint sentences. The mistake sentence contains a factual error and the hint sentence points to the mistake sentences."
    instruction = "Find the only mistake sentences and the corresponding hint sentences in the article. The mistake sentence introduces a factual error, while the hint sentence clarifies or corrects that error by directly addressing the information provided in the mistake sentence."
    
    ds = getDataset()
    
    article = ds[0]['marked_article']
    
    prompt = instruction + "\nArticle:\n" + article
    # prompt = "Where is the capital city of France."
    
    # print(prompt)
    
    response = getResponse(prompt, max_new_tokens=100)
    print(response)
    
if __name__ == "__main__":
    main()
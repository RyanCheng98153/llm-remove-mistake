import json
import sys
from difflib import SequenceMatcher

# Function to calculate LCS length
def lcs_length(seq1, seq2):
    matcher = SequenceMatcher(None, seq1, seq2)
    match = matcher.find_longest_match(0, len(seq1), 0, len(seq2))
    return match.size

# Function to perform similarity comparison and output to a file
def compare_answers(n_id, filepath='merge.json'):
    # Load data from JSON file
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    results = []

    for i in range(len(data)):
        n = i
        print(n)
        # Find the answer of id = n
        reference_item = data[n]
        if not reference_item:
            print(f"Item with id = {n} not found.")
            return

        # Split the reference answer into words
        answer1 = reference_item['answer'].split()

        # Calculate LCS score between answer1 and each other answer
        for item in data:
            if item['id'] == n:
                continue
            answer2 = item['answer'].split()
            lcs_len = lcs_length(answer1, answer2)
            score = lcs_len / len(answer1) if answer1 else 0
            results.append({"i": n, "j": item['id'], "score": score, "lcs": lcs_len, "strlen": len(answer1)})

    # Write results to file ans_{n}.txt
    output_filename = f'valid.txt'
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        for result in results:
            outfile.write(f"{result['i']}, {result['j']}: {result['score']:.4f} ({result['lcs']} / {result['strlen']})\n")
    
    print(f"Results saved to {output_filename}")
    
    # Sort the results by score in descending order
    sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
    print(f"Top 10 most similar data:")
    for i in range(10):
        print(f"({sorted_results[i]['i']}, {sorted_results[i]['j']}),\t lcs_score: {sorted_results[i]['score']:.3f} ({sorted_results[i]['lcs']} / {sorted_results[i]['strlen']})")
    
    sorted_filename = f'valid_sorted.txt'
    with open(sorted_filename, 'w', encoding='utf-8') as outfile:
        for result in sorted_results:
            id_str = f"{result['i']:<6}" + ", " + f"{result['j']:<6}"
            outfile.write(f"{id_str} LCS: {result['score']:.4f} ({result['lcs']} / {result['strlen']})\n")
    
    print(f"Sorted Results saved to {sorted_filename}")
    
    
# Input: specify n (the id to compare) here
n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
if not n or type(n) != int:
    n = 1
    
filepath = sys.argv[1] if len(sys.argv) > 1 else './merge.json'

compare_answers(n_id=n, filepath=filepath)
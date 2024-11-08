import json
import sys
from difflib import SequenceMatcher
from multiprocessing import Pool, Manager
from functools import partial
import os

# Function to calculate LCS length
def lcs_length(seq1, seq2):
    matcher = SequenceMatcher(None, seq1, seq2)
    match = matcher.find_longest_match(0, len(seq1), 0, len(seq2))
    return match.size

# Function to perform similarity comparison and output to files
def compare_answers(n_id, filepath='merge.json', target='answer', all_results=None):
    # Load data from JSON file
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)

    results = []

    # Define the range for this batch of data
    n_end = n_id + 100 if n_id + 100 < len(data) else len(data)

    for i in range(n_id, n_end):
        # Find the answer of id = i
        reference_item = data[i]
        if not reference_item:
            print(f"Item with id = {i} not found.")
            continue

        # Split the reference answer into words
        answer1 = reference_item[target].split()

        # Calculate LCS score between answer1 and each other answer
        for item in data:
            if item['id'] == i:
                continue
            answer2 = item[target].split()
            lcs_len = lcs_length(answer1, answer2)
            score = lcs_len / len(answer1) * 100 if answer1 else 0
            results.append({"i": i, "j": item['id'], "score": score, "lcs": lcs_len, "strlen": len(answer1)})

    # Append batch results to shared all_results list
    if all_results is not None:
        all_results.extend(results)

    # Output directory
    output_dir = f'./valid/{target}/'
    os.makedirs(output_dir, exist_ok=True)

    # Output results to a file every 100 iterations
    output_filename = f'{output_dir}{target}_{n_id // 100}.txt'
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        for result in results:
            outfile.write(f"{result['i']:<6}, {result['j']:<6}: {result['score']:<6.2f}% ({result['lcs']} / {result['strlen']})\n")
    print(f"Results saved to {output_filename}")

# Entry point for multi-process execution
if __name__ == '__main__':
    target = sys.argv[2] if len(sys.argv) > 2 else 'answer'
    filepath = sys.argv[1] if len(sys.argv) > 1 else './merge.json'

    # Load data to determine the length for range division
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Define the ranges for each process to handle 100 items at a time
    start_ids = [i * 100 for i in range((len(data) + 99) // 100)]

    # Use Manager to create a shared list for collecting all results
    with Manager() as manager:
        all_results = manager.list()  # Shared list to store results across processes

        # Use multiprocessing to parallelize the task
        with Pool(processes=4) as pool:  # Adjust the number of processes as needed
            # Use partial to fix filepath and target, so only n_id is passed to each process
            pool.map(partial(compare_answers, filepath=filepath, target=target, all_results=all_results), start_ids)

        # Sort all results by score in descending order after processing all batches
        sorted_results = sorted(all_results, key=lambda x: x['score'], reverse=True)

        # Print top 100 most similar data
        print(f"Top 100 most similar data:")
        for i in range(min(100, len(sorted_results))):
            print(f"({sorted_results[i]['i']}, {sorted_results[i]['j']}),\t lcs_score: {sorted_results[i]['score']:<6.2f}% ({sorted_results[i]['lcs']} / {sorted_results[i]['strlen']})")

        # Save sorted results to file
        sorted_filename = 'valid_sorted.txt'
        with open(sorted_filename, 'w', encoding='utf-8') as outfile:
            for result in sorted_results:
                id_str = f"{result['i']:<6}" + ", " + f"{result['j']:<6}"
                outfile.write(f"{id_str} LCS: {result['score']:<6.2f}% ({result['lcs']} / {result['strlen']})\n")

        print(f"Sorted Results saved to {sorted_filename}")

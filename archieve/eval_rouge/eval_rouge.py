import re
def split_into_sentences(text):
    # Regular expression pattern, based on periods, question marks, and exclamation marks
    sentence_endings = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s'
    return re.split(sentence_endings, text)    

from rouge_score import rouge_scorer

# Function to calculate ROUGE-L score using rouge-score library
def cal_rougeL(reference, hypothesis):
    scorer:rouge_scorer.RougeScorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = scorer.score(reference, hypothesis)
    return scores['rougeL'].fmeasure  # Return only the f1-measure of ROUGE-L

def cal_rougeL_precision(reference, hypothesis):
    scorer:rouge_scorer.RougeScorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = scorer.score(reference, hypothesis)
    return scores['rougeL'].precision  # Return only the f1-measure of ROUGE-L


def cal_rougeL_recall(reference, hypothesis):
    scorer:rouge_scorer.RougeScorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = scorer.score(reference, hypothesis)
    return scores['rougeL'].recall  # Return only the f1-measure of ROUGE-L

def cal_rougeL_fmeasure(reference, hypothesis):
    scorer:rouge_scorer.RougeScorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = scorer.score(reference, hypothesis)
    return scores['rougeL'].fmeasure  # Return only the f1-measure of ROUGE-L

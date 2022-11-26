from datasets import load_dataset
import random
import itertools
from itertools import islice
import sys
import time
from tqdm import tqdm, trange
import re
import json
import ndjson


def batch_loader(seq, size):
    """
    Iterator that takes in a list `seq` and returns
    chunks of size `size` """
    return [seq[pos:pos + size] for pos in range(0, len(seq), size)]


def parse_meta(instance): 
    instance["meta"] = json.loads(instance["meta"])
    return instance

def filter_arxiv_text(instance): 
    keywords = ["\\part{", "\\chapter{", "\\section{", "\\section*{", "\\subsection{", "\\subsection*{", "\\subsubsection{", 
            "\\subsubsection*{", "\\paragraph{", "\\subparagraph{"]

    return any(x in instance["text"] for x in keywords) and "gnuplot" not in instance["text"]

def process_arxiv_text(instance): 
    text = instance["text"]

    rexp = re.compile(r"\\begin{bibdiv}.*?\\end{bibdiv}", re.DOTALL)
    text = re.sub(rexp, "", instance["text"])

    rexp = re.compile(r"\n{3,}", re.DOTALL)
    text = re.sub(rexp, "\n\n\n", text)

    instance["text"] = text

    return instance


def main(split): 
    """
    `split` is `"train"` or `"validation"`
    """
    arxiv = load_dataset("aggregator.py", "arxiv")

    print("PARSING ARXIV")
    print("loading into memory...")
    data_list = list(tqdm(arxiv[split]))
    print("processing...")
    data_list = list(filter(filter_arxiv_text, tqdm(data_list)))
    data_list = list(map(process_arxiv_text, tqdm(data_list)))
    data_list = list(map(parse_meta, tqdm(data_list)))

    #open("arxiv_examples.txt", "w").write("\n".join(["#"*80 + "\n" + x["text"] for x in eval_list[:100]]))

    keywords = ["formal", "books", "wiki", "stack-exchange", "math-dataset"]
    
    print("LOADING REST OF DATA...")
    data_rest = [load_dataset("aggregator.py", x)[split] for x in keywords]
    data_rest_list = list(itertools.chain.from_iterable(data_rest))
    data_rest_list = list(map(parse_meta, tqdm(data_rest_list)))
    
    data_list = data_list + data_rest_list
    print("shuffling...")
    random.shuffle(data_list)

    if split=="train": 
        for i, batch in enumerate(batch_loader(data_list, 100_000)):
            with open(f"proofpile_train_{i}.jsonl", "w") as f: 
                ndjson.dump(batch, f)

    elif split=="validation": 
        cut_idx = len(data_list)//2

        with open("proofpile_dev.jsonl", "w") as f: 
            ndjson.dump(data_list[:cut_idx], f)
        with open("proofpile_test.jsonl", "w") as f: 
            ndjson.dump(data_list[cut_idx:], f)
            
    print("COMPLETE")

if __name__=="__main__": 
    main("train")
    main("validation")

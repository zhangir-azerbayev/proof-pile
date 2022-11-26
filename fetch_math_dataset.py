import os
import sys
import json
import ndjson
from pathlib import Path
from fetch_mathoverflow import batch_loader
import random

from utils import make_archive

ARCHIVE_URL = "https://people.eecs.berkeley.edu/~hendrycks/MATH.tar"
SAVE_PATH = "math-dataset"

random.seed(20)

def main():  
    VAL_RATE=5e-2
    Path(SAVE_PATH).mkdir(exist_ok=True)

    archive_path = os.path.join(SAVE_PATH, "archive.tar")
    os.system("wget -O " + archive_path + " " + ARCHIVE_URL)
    os.system("tar -xf " + archive_path + " -C " + SAVE_PATH)
    
    cat_dir = os.path.join(SAVE_PATH, "MATH/train")

    for cat_name in os.listdir(cat_dir): 
        cat_path = os.path.join(cat_dir, cat_name)
        if os.path.isdir(cat_path):
            cat_texts = []
            for f in os.listdir(cat_path): 
                f_path = os.path.join(cat_path, f)

                with open(f_path) as fle: 
                    prob_json = json.load(fle)

                text = "{\\bf Problem.} " + prob_json["problem"] + "\n" +\
                       "{\\bf Level.} " + prob_json["level"] + "\n" +\
                       "{\\bf Type.} " + prob_json["type"] + "\n" +\
                       "{\\bf Solution.} " + prob_json["solution"]

                cat_texts.append(text)

        random.shuffle(cat_texts) 
        instances = [{"text": x.strip(), "meta": {"set_name": "MATH"}} for x in cat_texts]
        split = int(VAL_RATE*len(instances))
        train = instances[split:]
        val = instances[:split]

        with open(os.path.join(SAVE_PATH, "train.jsonl"), "a+") as f: 
            f.write(ndjson.dumps(train))
            f.write("\n")
        with open(os.path.join(SAVE_PATH, "val.jsonl"), "a+") as f: 
            f.write(ndjson.dumps(val))
            f.write("\n")

    os.system("gzip " + os.path.join(SAVE_PATH, "train.jsonl"))
    os.system("gzip " + os.path.join(SAVE_PATH, "val.jsonl"))
    os.system("rm -r " + os.path.join(SAVE_PATH, "MATH"))
    os.remove(archive_path)

if __name__=="__main__": 
    main()

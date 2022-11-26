from bs4 import BeautifulSoup as bs
import os
import wikipediaapi
import sys
import re
import pypandoc
import json
from pathlib import Path

from fetch_books_and_formal import _download_with_progress_bar
from utils import make_archive

import random

random.seed(20)


def page_titles_of_category(cat_page):
        """
        recursively
        """
        titles = []
        for member in cat_page.categorymembers.values(): 
            if member.ns == wikipediaapi.Namespace.MAIN: 
                titles.append(member.title)
            elif member.ns == wikipediaapi.Namespace.CATEGORY: 
                titles += page_titles_of_category(member)
        return titles

def wikipedia(): 
    """
    this doesnt work dont run it
    """
    init_categories = [
        #"Category:Mathematical_theorems",
        "Category:Mathematical_proofs",
        #"Category:Mathematical_examples",
        #"Category:Mathematical_problems",
        #"Category:Mathematical_terminology",
    ]

    title_set = set()
    for cat_name in init_categories: 
        print(cat_name + "...")
        title_set = title_set.union(page_titles_of_category(wiki.page(cat_name)))
    

PROOFWIKI_URL = (
    "https://zenodo.org/record/4902289/files/naturalproofs_proofwiki.json?download=1"
)
def proofwiki(testing=False):
    VAL_RATE = 0.025
    save_dir = "wiki/proofwiki"
    val_dir = "wiki/proofwiki_val"
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    Path(val_dir).mkdir(parents=True, exist_ok=True)

    if testing:
        with open("naturalproofs/proofwiki.json") as f:
            struct = json.load(f)
    else:
        print("DOWNLOADING PROOFWIKI")
        resp = _download_with_progress_bar(PROOFWIKI_URL)
        struct = json.loads(resp.decode("utf-8"))
        print("DONE DOWNLOADING PROOFWIKI")
    
    for i, thm in enumerate(struct["dataset"]["theorems"]):
        if thm["contents"]:
            thm_string = "\\section{" + thm["label"] + "}\n"
            thm_string += (
                "Tags: " + ", ".join(thm["categories"]).replace("/", ": ") + "\n\n"
            )

            thm_string += (
                "\\begin{theorem}\n"
                + "\n".join(thm["contents"])
                + "\n\\end{theorem}\n\n"
            )

            for proof in thm["proofs"]:
                thm_string += (
                    "\\begin{proof}\n"
                    + "\n".join(proof["contents"])
                    + "\n\\end{proof}\n\n"
                )

            if random.random()>VAL_RATE: 
                with open(os.path.join(save_dir, f"""thm_{thm["id"]}.txt"""), "w") as f:
                    f.write(thm_string)
            else: 
                with open(os.path.join(val_dir, f"""thm_{thm["id"]}.txt"""), "w") as f: 
                    f.write(thm_string)

    defn_strings = []
    for defn in struct["dataset"]["definitions"]:
        if defn["contents"]:
            defn_string = (
                "\\begin{definition}["
                + defn["label"]
                + "]\n"
                + "\n".join(defn["contents"])
                + "\n\\end{definition}").strip()
            
            if random.random()>VAL_RATE:
                with open(os.path.join(save_dir, f"""def_{defn["id"]}.txt"""), "w") as f:
                    f.write(defn_string)
            else: 
                with open(os.path.join(val_dir, f"""def_{defn["id"]}.txt"""), "w") as f: 
                    f.write(defn_string)
              

if __name__=="__main__": 
    #wikipedia()
    proofwiki()
    make_archive("wiki/proofwiki")
    make_archive("wiki/proofwiki_val")

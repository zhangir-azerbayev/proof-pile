#!/bin/sh
python fetch_books_and_formal.py
python fetch_math_dataset.py
python fetch_stack_exchange.py
python fetch_wiki.py
python fetch_arxiv.py

python gen_split.py

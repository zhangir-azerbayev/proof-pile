---
annotations_creators:
- no-annotation
language:
- en
language_creators:
- found
license: []
multilinguality:
- monolingual
pretty_name: proof-pile
size_categories: []
source_datasets: []
tags:
- math
- mathematics
- formal-mathematics
task_categories:
- text-generation
task_ids:
- language-modeling
---

# Dataset Description
The `proof-pile` is a 40GB pre-training dataset of mathematical text that comprises roughly 15 billion tokens. The dataset is composed of diverse sources of both informal and formal mathematics, namely
- ArXiv.math (37GB)
- Open-source math textbooks (50MB)
- Formal mathematics libraries (500MB)
    - Lean mathlib and other Lean repositories 
    - Isabelle AFP
    - Coq mathematical components and other Coq repositories 
    - HOL Light
    - set.mm
    - Mizar Mathematical Library
- Math Overflow and Math Stack Exchange (500MB)
- Wiki-style sources (50MB)
  - ProofWiki
  - Wikipedia math articles
- MATH dataset (6MB)

# Supported Tasks
This dataset is intended to be used for pre-training language models. We envision models pre-trained on the `proof-pile` will have many downstream applications, including informal quantitative reasoning, formal theorem proving, semantic search for formal mathematics, and autoformalization. 

# Languages
All informal mathematics in the `proof-pile` is written in English and LaTeX (arXiv articles in other languages are filtered out using [languagedetect](https://github.com/shuyo/language-detection/blob/wiki/ProjectHome.md)). Formal theorem proving languages represented in this dataset are Lean 3, Isabelle, Coq, HOL Light, Metamath, and Mizar.

 # Configurations
 The data is sorted into `"arxiv", "books", "formal", "stack-exchange", "wiki",` and `"math-dataset"` configurations. This is so that it is easy to upsample particular configurations during pre-training with the `datasets.interleave_datasets()` function. 
 
# Evaluation
The version of `set.mm` in this dataset has 10% of proofs replaced with the `?` character in order to preserve a validation and test set for Metamath provers pre-trained on the `proof-pile`. The precise split can be found here: [validation](https://github.com/zhangir-azerbayev/mm-extract/blob/main/valid_decls.json) and [test](https://github.com/zhangir-azerbayev/mm-extract/blob/main/test_decls.json). 

The Lean mathlib commit used in this dataset is `6313863`. Theorems created in subsequent commits can be used for evaluating Lean theorem provers. 

This dataset contains only the training set of the [MATH dataset](https://github.com/hendrycks/math). However, because this dataset contains ProofWiki, the Stacks Project, Trench's Analysis, and Stein's Number Theory, models trained on it cannot be evaluated on the [NaturalProofs dataset](https://github.com/wellecks/naturalproofs). 

## Contributions
Authors: Zhangir Azerbayev, Edward Ayers, Bartosz Piotrowski. 

We would like to thank Jeremy Avigad, Albert Jiang, and Wenda Li for their invaluable guidance, and the Hoskinson Center for Formal Mathematics for its support. 

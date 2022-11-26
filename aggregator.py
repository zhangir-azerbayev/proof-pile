# Copyright 2020 The HuggingFace Datasets Authors and the current dataset script contributor.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# TODO: Address all TODOs and remove all explanatory comments
"""TODO: Add a description here."""


import csv
import json
import ndjson
import os
import sys # just for debugging, delete

import itertools
from itertools import islice

import datasets


# TODO: Add BibTeX citation
# Find for instance the citation on arxiv or on the dataset repo/website
_CITATION = """\
@InProceedings{huggingface:dataset,
title = {A great new dataset},
author={huggingface, Inc.
},
year={2020}
}
"""

# TODO: Add description of the dataset here
# You can copy an official description
_DESCRIPTION = """\
This new dataset is designed to solve this great NLP task and is crafted with a lot of care.
"""

# TODO: Add a link to an official homepage for the dataset here
_HOMEPAGE = ""

# TODO: Add the licence for the dataset here if you can find it
_LICENSE = ""

# TODO: Add link to the official dataset URLs here
# The HuggingFace Datasets library doesn't host the datasets but only points to the original files.
# This can be an arbitrary nested dict/list of URLs (see below in `_split_generators` method)
_URLS = {
    "first_domain": "https://huggingface.co/great-new-dataset-first_domain.zip",
    "second_domain": "https://huggingface.co/great-new-dataset-second_domain.zip",
}


# TODO: Name of the dataset usually match the script name with CamelCase instead of snake_case
class ProofPile(datasets.GeneratorBasedBuilder):
    """TODO: Short description of my dataset."""

    VERSION = datasets.Version("1.1.0")

    # This is an example of a dataset with multiple configurations.
    # If you don't want/need to define several sub-sets in your dataset,
    # just remove the BUILDER_CONFIG_CLASS and the BUILDER_CONFIGS attributes.

    # If you need to make complex sub-parts in the datasets with configurable options
    # You can create your own builder configuration class to store attribute, inheriting from datasets.BuilderConfig
    # BUILDER_CONFIG_CLASS = MyBuilderConfig

    # You will be able to load one or the other configurations in the following list with
    # data = datasets.load_dataset('my_dataset', 'first_domain')
    # data = datasets.load_dataset('my_dataset', 'second_domain')
    BUILDER_CONFIGS = [
    datasets.BuilderConfig(name="arxiv", version=VERSION, description="All of English arxiv.math up to 03/22"),
    datasets.BuilderConfig(name="books", version=VERSION, description="Open source math textbooks"),
    datasets.BuilderConfig(name="formal", version=VERSION, description="Formal math libraries"), 
    datasets.BuilderConfig(name="stack-exchange", version=VERSION, description="math overflow and math stack exchange"), 
    datasets.BuilderConfig(name="wiki", version=VERSION, description="wikipedia articles and proofwiki."), 
    datasets.BuilderConfig(name="math-dataset", version=VERSION, description="the MATH dataset."), 
    ]


    def _info(self):
        # TODO: This method specifies the datasets.DatasetInfo object which contains informations and typings for the dataset
        features = datasets.Features(
            {
                "text": datasets.Value("string"),
                "meta": datasets.Value("string")
                # These are the features of your dataset like images, labels ...
            }
        )
        return datasets.DatasetInfo(
            # This is the description that will appear on the datasets page.
            description=_DESCRIPTION,
            # This defines the different columns of the dataset and their types
            features=features,  # Here we define them above because they are different between the two configurations
            # If there's a common (input, target) tuple from the features, uncomment supervised_keys line below and
            # specify them. They'll be used if as_supervised=True in builder.as_dataset.
            # supervised_keys=("sentence", "label"),
            # Homepage of the dataset for documentation
            homepage=_HOMEPAGE,
            # License for the dataset if available
            license=_LICENSE,
            # Citation for the dataset
            citation=_CITATION,
        )

    def _split_generators(self, dl_manager):
        # TODO: This method is tasked with downloading/extracting the data and defining the splits depending on the configuration
        # If several configurations are possible (listed in BUILDER_CONFIGS), the configuration selected by the user is in self.config.name

        # dl_manager is a datasets.download.DownloadManager that can be used to download and extract URLS
        # It can accept any type or nested list/dict and will give back the same structure with the url replaced with path to local files.
        # By default the archives will be extracted and a path to a cached folder where they are extracted is returned instead of the archive

        self.archived_configs = ["arxiv", "wiki"]
        self.jsonl_configs = ["stack-exchange", "math-dataset", "books", "formal"]

        if self.config.name in self.archived_configs: 
            if self.config.name=="arxiv": 
                with open(dl_manager.download("splits.json")) as f: 
                    split = json.load(f)

                train_paths = split["arxiv-train"]
                val_paths = split["arxiv-valid"]
            if self.config.name=="stack-exchange": 
                train_paths = [os.path.join("./stack-exchange", x) for x in ["math_overflow.tar.gz",
                    "math_stack_exchange.tar.gz"]]
                val_paths = [os.path.join("./stack-exchange", x) for x in ["math_overflow_val.tar.gz",
                    "math_stack_exchange_val.tar.gz"]]
            if self.config.name=="math-dataset": 
                train_paths = ["math-dataset/train.tar.gz"]
                val_paths = ["math-dataset/val.tar.gz"]
            if self.config.name=="wiki": 
                train_paths = ["wiki/proofwiki.tar.gz", "wiki/wikipedia.tar.gz"]
                val_paths = ["wiki/proofwiki_val.tar.gz"]

            train_files = itertools.chain.from_iterable(dl_manager.iter_archive(dl_manager.download(x)) for x in train_paths)
            val_files = itertools.chain.from_iterable(dl_manager.iter_archive(dl_manager.download(x)) for x in val_paths)
 
            return [
                datasets.SplitGenerator(
                    name=datasets.Split.TRAIN,
                    # These kwargs will be passed to _generate_examples
                    gen_kwargs={
                        "data_files": train_files,
                    },
                ),
                datasets.SplitGenerator(
                    name=datasets.Split.VALIDATION, 
                    # These kwargs will be passed to _generate_examples
                    gen_kwargs={
                        "data_files": val_files,
                    },
                ),
            ]

        elif self.config.name in self.jsonl_configs: 
            if self.config.name=="stack-exchange": 
                exchanges = ["math_overflow", "math_stack_exchange", "cstheory_stack_exchange", 
                        "physics_stack_exchange", "proofassistants_stack_exchange"]

                train_paths = [os.path.join("./stack-exchange", x, "train.jsonl.gz") for x in exchanges]
                val_paths = [os.path.join("./stack-exchange", x, "val.jsonl.gz") for x in exchanges]
            elif self.config.name=="math-dataset":
                train_paths = ["./math-dataset/train.jsonl.gz"]
                val_paths = ["./math-dataset/val.jsonl.gz"]
            elif self.config.name=="books": 
                books = ["cam", "cring", "hott", "napkin", "stacks", "stein", "trench"]
                train_paths = [os.path.join("./books", x + "_train.jsonl.gz") for x in books]
                val_paths = [os.path.join("./books", x+"_val.jsonl.gz") for x in books]
            elif self.config.name=="formal": 
                libs = ["afp",  "coq", "hol", "lean", "mizar", "setmm"]
                train_paths = [os.path.join("./formal", x + "_train.jsonl.gz") for x in libs]
                val_paths = [os.path.join("./formal", x + "_val.jsonl.gz") for x in libs]
 
            train_files = itertools.chain.from_iterable([dl_manager.download_and_extract(x)] for x in train_paths)
            val_files = itertools.chain.from_iterable([dl_manager.download_and_extract(x)] for x in val_paths)

            return [
                datasets.SplitGenerator(
                    name=datasets.Split.TRAIN,
                    # These kwargs will be passed to _generate_examples
                    gen_kwargs={
                        "data_files": train_files,
                    },
                ),
                datasets.SplitGenerator(
                    name=datasets.Split.VALIDATION, 
                    # These kwargs will be passed to _generate_examples
                    gen_kwargs={
                        "data_files": val_files,
                    },
                ),
            ]
        else: 
            with open(dl_manager.download("splits.json")) as f: 
                splits = json.load(f)

            return [
                datasets.SplitGenerator(
                    name=datasets.Split.TRAIN,
                    # These kwargs will be passed to _generate_examples
                    gen_kwargs={
                        "data_files": [dl_manager.download(x) for x in splits[self.config.name + "-train"]],
                    },
                ),
                datasets.SplitGenerator(
                    name=datasets.Split.VALIDATION, 
                    # These kwargs will be passed to _generate_examples
                    gen_kwargs={
                        "data_files": [dl_manager.download(x) for x in splits[self.config.name + "-valid"]],
                    },
                ),
            ]

    # method parameters are unpacked from `gen_kwargs` as given in `_split_generators`
    def _generate_examples(self, data_files):
        # TODO: This method handles input defined in _split_generators to yield (key, example) tuples from the dataset.
        # The `key` is for legacy reasons (tfds) and is not important in itself, but must be unique for each example.
        key = 0 
        if self.config.name in self.archived_configs: 
            for name, obj in data_files: 
                text = obj.read().decode()
                # Yields examples as (key, example) tuples 
                yield key, {
                    "text": text,
                    "meta": json.dumps({
                        "config": self.config.name, 
                        "file": name, 
                    })
                }
                key += 1
        elif self.config.name in self.jsonl_configs: 
            key = 0 
            for name in data_files: 
                with open(name) as f: 
                    instances = ndjson.load(f)
                for instance in instances: 
                    yield key, {"text": instance["text"], 
                            "meta": json.dumps(instance["meta"])}
                    key += 1 
        else: 
            for name in data_files: 
                with open(name, encoding="utf-8") as f:
                    text = f.read()
                # Yields examples as (key, example) tuples
                yield key, {
                    "text": text,
                    "meta": json.dumps({
                        "config": self.config.name, 
                        "file": name, 
                    })
                }
            key += 1

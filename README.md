# Building the `proof-pile`
Code and instructions for building the `proof-pile` from raw data downloaded from the web. This repository exists primarily for reproducibility puproses. If you wish to simply use the `proof-pile` or learn more about its composition, please see the [Huggingface datasets page](https://huggingface.co/datasets/hoskinson-center/proof-pile).  

## Replication instructions
To download the data, first create an [Amazon S3](https://aws.amazon.com/s3/) account and set up the [S3cmd](https://s3tools.org/s3cmd) command line utility. This is required to download ArXiv source files. Note that using Amazon S3 will incur a fee. Next, authenticate with the [Github REST API](https://docs.github.com/en/rest/guides/getting-started-with-the-rest-api) to avoid running into the rate limit. 

Running `./download.sh` will download all the corpus's raw data using Amazon S3, the Github REST API, and standard HTTP
requests. This script also takes care of the bulk ofpreprocessing. Finally, running `make_jsons.py` will assemble the
full training, validation, and test sets from local files, apply some minor preprocessing, and dump the data into
`.jsonl.gz` files. These archives are identical to the files accessed by the Huggingface dataset. 

## Analysis
The notebook `analysis/arxiv_noisedetection.ipynb` describes a method for detecting noise in the large and heterogeneous
arXiv subset of the data. 


## Contributions
Authors: Zhangir Azerbayev, Edward Ayers, Bartosz Piotrowski. 

We would like to thank Jeremy Avigad, Albert Jiang, and Wenda Li for their invaluable guidance, and the Hoskinson Center for Formal Mathematics for its support. 

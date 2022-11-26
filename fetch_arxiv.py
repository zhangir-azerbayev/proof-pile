import os
import sys 
from pathlib import Path
import datetime

import tarfile
import xml.etree.ElementTree as ET 
from tqdm import tqdm
import re 
from itertools import chain, islice
import requests
import time

import shutil

import arxiv 

import langdetect
from langdetect import detect

from utils import Loader as Loader
from utils import make_archive

def batch_loader(seq, size):
    """
    Iterator that takes in a list `seq` and returns
    chunks of size `size` 
    """
    return [seq[pos:pos + size] for pos in range(0, len(seq), size)]


def _delete_files_except_pattern(path, pattern, transform = lambda x: None, verbose=False):
    """
    recursively
    """
    for f in os.listdir(path):
        f_path = os.path.join(path, f)
        if verbose: 
            print(f_path)
        if os.path.isfile(f_path): 
            if not re.search(pattern, f):
                os.chmod(f_path, 0o755)
                os.remove(f_path)
            else: 
                transform(f_path)
        elif os.path.isdir(f_path):
            try: 
                print(f_path)
            except UnicodeEncodeError: 
                new_path = f_path.encode("utf-8", 'replace').decode()
                os.system(f"mv \"{f_path}\" \"{new_path}\"")
                f_path = new_path

            _delete_files_except_pattern(f_path, pattern, transform=transform, verbose=verbose)

def _download_with_progress_bar(url):
    response = requests.get(url, stream=True)
    total_size_in_bytes = int(response.headers.get("content-length", 0))
    block_size = 1024  # 1 Kibibyte
    progress_bar = tqdm(total=total_size_in_bytes, unit="iB", unit_scale=True)
    to_return = bytearray()
    for data in response.iter_content(block_size):
        progress_bar.update(len(data))
        to_return += data
    progress_bar.close()
    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        raise AssertionError("ERROR, something went wrong")

    return to_return

def get_math_ids(resumption_token="init"): 
    with Loader(f"fetching metadata shard {resumption_token}..."):
        if resumption_token=="init": 
            resp = requests.get("https://export.arxiv.org/oai2?verb=ListIdentifiers&set=math&metadataPrefix=oai_dc")
        else: 
            time.sleep(5)
            resp = requests.get(f"https://export.arxiv.org/oai2?verb=ListIdentifiers&resumptionToken={resumption_token}")
     
    root = ET.fromstring(resp.content.decode("utf-8"))
    articles = root[2]

    math_ids = {}
    for article in articles: 
        if article.tag == "{http://www.openarchives.org/OAI/2.0/}resumptionToken": 
            if article.text: 
                return math_ids | get_math_ids(resumption_token=article.text)
            else: 
                return math_ids

        db_id = article[0].text
        eyed = db_id[db_id.rindex(":")+1:]
        math_ids[eyed] = True 

def clean_tex_file(path): 
    with open(path, encoding="utf-8") as f: 
        try: 
            src = f.read()
        except (UnicodeDecodeError, UnicodeError): 
            print(f"Decoding error at {path} with utf-8. Trying latin-1")
            try: 
                with open(path, encoding="latin-1") as fle: 
                    src = fle.read()
                    #print("latin-1 successful\n")
            except (UnicodeDecodeError, UnicodeError): 
                #print(f"Decoding error at {path} with latin-1. Trying utf-16")
                try: 
                    with open(path, encoding="utf-16") as fl: 
                        src = fl.read()
                        #print("utf-16 successful\n")
                except (UnicodeDecodeError, UnicodeError): 
                    #print(f"Decoding error at {path} with utf-16. Trying utf-32")
                    try: 
                        with open(path, encoding="utf-32") as f: 
                            src = f.read()
                    except (UnicodeDecodeError, UnicodeError): 
                        print(f"Decoding error at {path} with all of utf-8, 16, 32 and latin-1. Deleting this file")
                        print("This issue should only occur with a handful of quite old files. Continuing...\n")
                        return 

    end = re.search(r"\\end\{document\}", src)
    if end: 
        src = src[:end.span()[1]]

    bib = re.search(r"\\Refs|\\begin\{thebibliography\}", src)
    if bib:
        src = src[:bib.span()[0]]
    
    os.chmod(path, 0o755)
    with open(path, "w", encoding="utf-8") as f: 
        f.write(src)

def clean_tex_file_some_more(path): 
    with open(path) as f:
        text = f.read()

    text = re.sub(r"(?<!\\)%.*", "", text) # deletes comments

    match_obj = re.search(r"\\begin\{document\}", text)
    if match_obj: 
        text = text[match_obj.span()[0]:]

    match_obj = re.search(r"\\begin\{references\}", text)
    if match_obj: 
        text = text[:match_obj.span()[0]]

    text = text.strip()

    os.remove(path)
    if len(text)>280: 
        try: 
            print(path) 
        except UnicodeEncodeError: 
            path = path.encode('utf-8', 'replace').decode()

        try: 
            lang = detect(text)
        except langdetect.lang_detect_exception.LangDetectException: 
            # no linguistic features to analyze, delete
            return 
        
        if lang=="en": 
            with open(path, "w") as f: 
                f.write(text)
        else: 
            print("HIT NONENGLISH ARTICLE")

def process_tarball_old_scheme(tarball_name, save_dir): 
    tarball_path = os.path.join(save_dir, tarball_name)
    os.system("tar -xf " + tarball_path + " -C " + save_dir)

    last_ = tarball_name.rfind("_")
    second_last_ = tarball_name.rfind("_", 0, last_)
    subdir = tarball_name[second_last_+1:last_]
    
    subpath = os.path.join(save_dir, subdir)
    zipped_names = os.listdir(subpath)

    for zipped_name in zipped_names: 
        if zipped_name[-len(".gz"):]==".gz": 
            zipped_path = os.path.join(subpath, zipped_name)
            if re.match(r"math", zipped_name): 
                eyed = zipped_name[:-len(".gz")]
                if tarfile.is_tarfile(zipped_path): 
                    article_dir = os.path.join(subpath, eyed)
                    Path(article_dir).mkdir()
                    os.system("tar -xzf " + zipped_path + " -C " + article_dir)
                    os.remove(zipped_path)
                else: 
                    os.system("gzip -d " + zipped_path)
                    unzipped_path = os.path.join(subpath, eyed)
                    os.rename(unzipped_path, unzipped_path + ".tex")
            else: 
                os.remove(zipped_path)

    _delete_files_except_pattern(subpath, r".*\.tex", transform=clean_tex_file)
    os.remove(tarball_path)

def process_tarball(tarball_name, save_dir, math_ids): 
    tarball_path = os.path.join(save_dir, tarball_name)
    untar_cmd = "tar -xf " + tarball_path + " -C " + save_dir
    os.system(untar_cmd)
    
    last_ = tarball_name.rfind("_")
    second_last_ = tarball_name.rfind("_", 0, last_)
    subdir = tarball_name[second_last_+1:last_]
    
    subpath = os.path.join(save_dir, subdir)
    listdir = os.listdir(subpath)

    ids = [x[:-3] for x in listdir if x[-3:]==".gz"]
 
    for eyed in ids: 
        if eyed in math_ids: 
            zipped_path = os.path.join(subpath, eyed + ".gz")

            if tarfile.is_tarfile(zipped_path): 
                article_dir = os.path.join(subpath, eyed)
                Path(article_dir).mkdir()
                os.system("tar -xzf " + zipped_path + " -C " + article_dir)
                os.remove(zipped_path)
            else: 
                os.system("gzip -d " + zipped_path)
                unzipped_path = os.path.join(subpath, eyed)
                os.rename(unzipped_path, unzipped_path + ".tex")
    
    _delete_files_except_pattern(subpath, r".*\.tex", transform=clean_tex_file)
    os.remove(tarball_path)

def main(): 
    """
    Warning: this code is *extremely* brittle
    """
    math_ids = get_math_ids()

    save_dir = "arxiv"
    Path(save_dir).mkdir(exist_ok=True) 
    manifest_path = os.path.join(save_dir, "manifest.xml")
    
    os.system(f"s3cmd get s3://arxiv/src/arXiv_src_manifest.xml --requester-pays {manifest_path}") 

    tree = ET.parse(manifest_path)
    root = tree.getroot()
    
    shards_and_dates = []
    for child in root: 
        if child.tag == "file":
            shard = child[1].text # the index of filename
            yymm = child[9].text # the index of yymm
            shards_and_dates.append((shard, yymm))
 
    format_cutoff = datetime.datetime(2007, 3, 1) # arXiv switches from old to new format
    for shard, yymm in tqdm(shards_and_dates): 
        print("SHARD: ", shard)
        os.system(f"s3cmd get s3://arxiv/" + shard + \
                " --requester-pays " + save_dir) 
        tarball_name=shard[shard.rindex("/")+1:]
        
        # nb this code will stop working in 2051 ;) 
        year = int("19" + yymm[:2]) if int(yymm[:2])>50 else int("20"+yymm[:2])
        if datetime.datetime(year, int(yymm[2:]), 1)<=format_cutoff: 
            process_tarball_old_scheme(tarball_name, save_dir)
        else: 
            process_tarball(tarball_name, save_dir, math_ids) 

    os.remove(manifest_path)

if __name__=="__main__": 
    main()
    _delete_files_except_pattern("arxiv", r".*\.tex$", transform=clean_tex_file_some_more)
    for f in tqdm(os.listdir("arxiv")):
        f_path = os.path.join("arxiv", f)
        make_archive(f_path)

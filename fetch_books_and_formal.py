import sys
import os

import json
import ndjson
import re

from pathlib import Path
from tqdm import tqdm

import requests
from tqdm import tqdm

import base64

def jsonl_of_path(path, jsonl_train_path, jsonl_val_path, 
        train_split_key, val_split_key): 
    train_instances = []
    val_instances = []
    print("CREATING JSONL.GZ")
    with open("splits.json") as f: 
        splits = json.load(f)

    for root, dirs, files in tqdm(os.walk(path)): 
        for name in files: 
            this_path = os.path.join(root, name)
            with open(this_path) as f: 
                text = f.read()

            instance = {"text": text, 
                        "meta": {
                            "subset_name": "curated", 
                            "file": os.path.join(root, name)
                       }
            }

            if this_path in splits[train_split_key]: 
                train_instances.append(instance)
            elif this_path in splits[val_split_key]: 
                val_instances.append(instance)
            else: 
                raise KeyError("key not found in splits.json")


    with open(jsonl_train_path, "w") as f: 
        ndjson.dump(train_instances, f)
    os.system("gzip " + jsonl_train_path)

    with open(jsonl_val_path, "w") as f: 
        ndjson.dump(val_instances, f)
    os.system("gzip " + jsonl_val_path)

    os.system("rm -r " + path)
    print("succesful conversion to jsonl")


def check_encoding(path): 
    for f in os.listdir(path): 
        f_path = os.path.join(path, f)
        if os.path.isfile(f_path): 
            with open(f_path, encoding="utf-8") as fle: 
                try: 
                    fle.read()
                except UnicodeDecodeError: 
                    print(f"{f_path} is not unicode")
        elif os.path.isdir(f_path): 
            check_encoding(f_path)


def _get_dir_from_repo(author, repo, sha, repo_dir, save_path, creds):
    """
    This super unelegant solution is to get around the github api rate limit

    repo_dir must be top-level in the repo.
    """
    Path(save_path).mkdir(parents=True, exist_ok=True)
    archive_path = os.path.join(save_path, "archive.tar.gz")
    tarball_url = (
        "https://github.com/" + author + "/" + repo + "/archive/" + sha + ".tar.gz"
    )

    os.system("wget -O " + archive_path + " " + tarball_url)
    os.system("tar -xzf " + archive_path + " -C " + save_path)

    export_name = repo + "-" + sha

    os.system(
        "cp -r " + os.path.join(save_path, export_name, repo_dir, "*") + " " + save_path
    )
    os.system("rm -r " + os.path.join(save_path, export_name) + " " + archive_path)


def _delete_files_except_pattern(path, pattern):
    """
    recursively
    """
    for f in os.listdir(path):
        f_path = os.path.join(path, f)
        if os.path.isfile(f_path):
            if not re.search(pattern, f):
                os.remove(f_path)
            else: # debugging
                with open(f_path, encoding="utf-8") as f: 
                    try: 
                        f.read()
                    except: 
                        print(f"{f_path} not unicode encoded")
        elif os.path.islink(f_path): 
            os.remove(f_path)
        elif os.path.isdir(f_path):
            _delete_files_except_pattern(f_path, pattern)


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


def _blob_to_text(blob, creds):
    resp = requests.get(blob["url"], auth=creds)
    if resp.status_code != 200:
        raise AssertionError("Failed to fetch from Github API")

    resp_json = json.loads(resp.content.decode("utf-8"))
    return base64.b64decode(resp_json["content"])


def lean(creds):
    save_dir = "formal/lean"
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    sources = [
        {
            "author": "leanprover-community",
            "repo": "mathlib",
            "sha": "63138639ca195344ae96aa77f3a02b90a3ac5c68",
            "repo_dir": "src",
            "save_path": os.path.join(save_dir, "mathlib"),
        },
        {
            "author": "leanprover-community",
            "repo": "lean-liquid",
            "sha": "9701fc4a29514852b599e9732c2409f34153ce2a",
            "repo_dir": "src",
            "save_path": os.path.join(save_dir, "liquid"),
        },
        {
            "author": "leanprover-community",
            "repo": "sphere-eversion",
            "sha": "cb378966c3c02d9e4ee83040d20c51782fa351ae",
            "repo_dir": "src",
            "save_path": os.path.join(save_dir, "sphere-eversion"),
        },
        {
            "author": "leanprover-community",
            "repo": "lftcm2020",
            "sha": "8b9f7c47b546227b7b6c877315e45eaccc2a0d70",
            "repo_dir": "src",
            "save_path": os.path.join(save_dir, "lftcm"),
        },
        {
            "author": "leanprover-community",
            "repo": "lean-perfectoid-spaces",
            "sha": "95a6520ce578b30a80b4c36e36ab2d559a842690",
            "repo_dir": "src",
            "save_path": os.path.join(save_dir, "perfectoid"),
        },
        {
            "author": "leanprover-community",
            "repo": "mathzoo",
            "sha": "87e9b492daeb929838706942aaa2437621b34a0e",
            "repo_dir": "src",
            "save_path": os.path.join(save_dir, "mathzoo"),
        },
    ]

    for source in sources:
        _get_dir_from_repo(**source, creds=creds)
        _delete_files_except_pattern(source["save_path"], r".*\.lean")

    # we also don't want meta code
    to_delete = ["tactic", "meta"]
    os.system(
        "rm -r " + " ".join([os.path.join(save_dir, "mathlib", x) for x in to_delete])
    )

    jsonl_of_path(save_dir, "formal/lean_train.jsonl", "formal/lean_val.jsonl", 
            "formal-train", "formal-valid")


def coq(creds):
    save_dir = "formal/coq"
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    sources = [
        {
            "author": "math-comp",
            "repo": "analysis",
            "sha": "2ae3b628d12cacdc000c4cd70e6f3cae26ecf429",
            "repo_dir": "theories",
            "save_path": os.path.join(save_dir, "analysis"),
        },
        {
            "author": "math-comp",
            "repo": "math-comp",
            "sha": "65519a110ffdad7869b2a7cd08a2ddb51161b377",
            "repo_dir": "mathcomp",
            "save_path": os.path.join(save_dir, "math-comp"),
        },
        {
            "author": "math-comp",
            "repo": "odd-order",
            "sha": "833261a01fd0c62b05ccbadfc0c682e0bc16a5e9",
            "repo_dir": "theories",
            "save_path": os.path.join(save_dir, "odd-order"),
        },
        {
            "author": "math-comp",
            "repo": "Abel",
            "sha": "61d79aeb0acc1855e22882c484b73645df53b746",
            "repo_dir": "theories",
            "save_path": os.path.join(save_dir, "abel"),
        },
    ]

    for source in sources:
        _get_dir_from_repo(**source, creds=creds)
        _delete_files_except_pattern(source["save_path"], r".*\.v")

    jsonl_of_path(save_dir, "formal/coq_train.jsonl", "formal/coq_val.jsonl", 
            "formal-train", "formal-valid")


def trench():
    save_dir = "books/trench"
    archive_path = os.path.join(save_dir, "trench.zip")
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    print("DOWNLOADING TRENCH")
    os.system(
        "wget -O "
        + archive_path
        + ' "https://digitalcommons.trinity.edu/cgi/viewcontent.cgi?filename=2&article=1006&context=mono&type=additional"'
    )
    print("DONE DOWNLOADING TRENCH")

    os.system("unzip " + archive_path + " -d " + save_dir)
    to_delete = ["trench.zip", "wtrench.sty", "SETEPS.TEX", "EPS"]
    os.system("rm -r " + " ".join([os.path.join(save_dir, f) for f in to_delete]))

    jsonl_of_path(save_dir, "books/trench_train.jsonl", "books/trench_val.jsonl", 
            "books-train", "books-valid")


def setmm(creds):
    save_dir = "formal/setmm"
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    headers = {
        "Accept": "application/vnd.git-lfs+json",
    }

    json_data = {
        "operation": "download",
        "transfer": [
            "basic",
        ],
        "objects": [
            {
                "oid": "ff1a12d49d4c68a05245bfd369af358b93c51b8c141419085bb5cef830f6eb7a",
                "size": 182269314,
            },
        ],
    }

    response = requests.post(
        "https://github.com/zhangir-azerbayev/mm-extract.git/info/lfs/objects/batch",
        headers=headers,
        json=json_data,
    )

    resp_json = response.json()

    download_url = resp_json["objects"][0]["actions"]["download"]["href"]

    encoded_src = _download_with_progress_bar(download_url)
    src = encoded_src.decode("utf-8")

    with open(os.path.join(save_dir, "set.mm"), "w") as f:
        f.write(src)

    jsonl_of_path(save_dir, "formal/setmm_train.jsonl", "formal/setmm_val.jsonl", 
            "formal-train", "formal-valid")


def stein(creds):
    save_dir = "books/stein"
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    print("DOWNLOADING STEIN")
    resp = _download_with_progress_bar(
        "https://api.github.com/repos/williamstein/ent/git/blobs/a70578277b1222c94dc395f7d5baaf9862afd166"
    )
    print("DONE DOWNLOADING STEIN")

    resp_json = json.loads(resp.decode("utf-8"))
    src_encoded = base64.b64decode(resp_json["content"])
    src = src_encoded.decode("utf-8")

    with open(os.path.join(save_dir, "stein.tex"), "w") as f:
        f.write(src)

    jsonl_of_path(save_dir, "books/stein_train.jsonl", "books/stein_val.jsonl", 
            "books-train", "books-valid")

def cam(): 
    save_dir = "books/cam"
    archive_path = os.path.join(save_dir, "cam.tar.gz")
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    os.system("wget -O " + archive_path + " https://github.com/dalcde/cam-notes/archive/06b2239.tar.gz")

    os.system ("tar -xf " + archive_path + " -C " + save_dir)
    export_name = "cam-notes-06b2239b006f14d833cca2434190ebbf9a304bc6/"
    os.system(
            "cp -r "
            + os.path.join(
                save_dir, export_name, "* ")
            + save_dir
    )
    os.system("rm -r " + os.path.join(save_dir, export_name))
    os.remove(archive_path)
    os.remove(os.path.join(save_dir, "header.tex"))

    _delete_files_except_pattern(save_dir, r".*\.tex")

    jsonl_of_path(save_dir, "books/cam_train.jsonl", "books/cam_val.jsonl", 
            "books-train", "books-valid")

def hol(testing=False):
    save_dir = "formal/hol"
    archive_path = os.path.join(save_dir, "hol.zip")
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    if not testing:
        os.system(
            "wget -O "
            + archive_path
            + " https://github.com/jrh13/hol-light/archive/538c62f.tar.gz"
        )

    os.system("tar -xvf " + archive_path + " -C " + save_dir)
    os.system(
        "mv "
        + os.path.join(
            save_dir, "hol-light-538c62f7cdb0df146752c83f85fa672ae3906b03/* "
        )
        + save_dir
    )
    os.system(
        "rm -r "
        + os.path.join(save_dir, "hol-light-538c62f7cdb0df146752c83f85fa672ae3906b03")
    )
    os.system("rm " + archive_path)

    # all top level files are metaprogramming, so delete them
    for f in os.listdir(save_dir):
        f_path = os.path.join(save_dir, f)
        if os.path.isfile(f_path):
            os.remove(f_path)

    os.system("rm -r formal/hol/Proofrecording")

    _delete_files_except_pattern(save_dir, r".*\.ml|.*\.doc")

    jsonl_of_path(save_dir, "formal/hol_train.jsonl", "formal/hol_val.jsonl", 
            "formal-train", "formal-valid")

def afp(testing=False):
    save_dir = "formal/afp"
    archive_path = os.path.join(save_dir, "afp.zip")
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    if not testing:
        os.system(
            "wget -O "
            + archive_path
            + " https://github.com/isabelle-prover/mirror-afp-2021-1/archive/5a85b23.tar.gz"
        )

    os.system("tar -xf " + archive_path + " -C " + save_dir)
    os.system(
        "mv "
        + os.path.join(
            save_dir,
            "mirror-afp-2021-1-5a85b23fb030c472d9a7b2d65a61e428f4eb8233/thys/* ",
        )
        + save_dir
    )
    os.system(
        "rm -r "
        + os.path.join(
            save_dir, "mirror-afp-2021-1-5a85b23fb030c472d9a7b2d65a61e428f4eb8233"
        )
    )
    os.system("rm " + archive_path)

    _delete_files_except_pattern(save_dir, r".*\.thy|.*\.tex")

    jsonl_of_path(save_dir, "formal/afp_train.jsonl", "formal/afp_val.jsonl", 
            "formal-train", "formal-valid")

def mizar(creds):
    save_dir = "formal/mizar"
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    resp = requests.get(
        "https://api.github.com/repos/zhangir-azerbayev/mizar-mirror/git/trees/ce8e9735fd7a4d3488069c48da76bc622aec46ec"
    )
    if resp.status_code != 200:
        raise AssertionError("Failed to fetch mizar from Github API")

    resp_json = resp.json()
    tree = resp_json["tree"]

    print("DOWNLOADING MIZAR")
    for blob in tqdm(tree):
        assert blob["type"] == "blob"

        src = _blob_to_text(blob, creds)
        src = src.decode("utf-8")
        # mml files have licensing information from lines 2-12
        src = "\n".join(
            [x for i, x in enumerate(src.split("\n")) if i not in range(2, 13)]
        )

        save_path = os.path.join(save_dir, blob["path"])
        with open(save_path, "w") as f:
            f.write(src)
    print("DONE DOWNLOADING MIZAR")

    jsonl_of_path(save_dir, "formal/mizar_train.jsonl", "formal/mizar_val.jsonl", 
            "formal-train", "formal-valid")


def hott(creds):
    save_dir = "books/hott"
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    resp = requests.get(
        "https://api.github.com/repos/HoTT/book/git/trees/781565e93979f926001a353bf4ee1284ffa4fcb0",
        auth=creds,
    )
    if resp.status_code != 200:
        raise AssertionError("Failed to fetch HoTT book from Github API")

    resp_json = resp.json()
    tree = resp_json["tree"]
    blobs = [blob for blob in tree if blob["type"] == "blob"]

    banned = [
        "back.tex",
        "bmpsize-hack.tex",
        "main.tex",
    ]

    banned_rgx = r"opt|cover|front|hott"

    print("DOWNLOADING HOTT BOOK")
    for blob in tqdm(blobs):
        if (
            blob["path"][-4:] == ".tex"
            and blob["path"] not in banned
            and not re.match(banned_rgx, blob["path"])
        ):
            src_enc = _blob_to_text(blob, creds)
            src = src_enc.decode("utf-8")

            save_path = os.path.join(save_dir, blob["path"])
            with open(save_path, "w") as f:
                f.write(src)

    print("DONE DOWNLOADING HOTT BOOK")

    jsonl_of_path(save_dir, "books/hott_train.jsonl", "books/hott_val.jsonl", 
            "books-train", "books-valid")

def stacks(creds):
    save_dir = "books/stacks"
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    resp = requests.get(
        "https://api.github.com/repos/stacks/stacks-project/git/trees/0a847ff5e41b47795be075e130e7810173b35933",
        auth=creds,
    )
    resp_json = json.loads(resp.content.decode("utf-8"))
    # assumes everything we need is a top level file, which is true for this commit.
    blobs = resp_json["tree"]
    print("DOWNLOADING STACKS")
    for blob in tqdm(blobs):
        if (
            blob["type"] == "blob"
            and blob["path"][-4:] == ".tex"
            and blob["path"] != "fdl.tex"
        ):
            decoded_content = _blob_to_text(blob, creds)
            with open(os.path.join(save_dir, blob["path"]), "wb") as f:
                f.write(decoded_content)
    print("DONE DOWNLOADING STACKS")

    jsonl_of_path(save_dir, "books/stacks_train.jsonl", "books/stacks_val.jsonl", 
            "books-train", "books-valid")

def cring(creds):
    save_dir = "books/cring"
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    resp = requests.get(
        "https://api.github.com/repos/aisejohan/cring/git/trees/2db2618ff70831002aeefbb16885ee42d5198db3",
        auth=creds,
    )
    if resp.status_code != 200:
        raise AssertionError("Failed to catch cring from Github API")

    trees = json.loads(resp.content.decode("utf-8"))["tree"]

    print("DOWNLOADING CRING")
    for blob in tqdm(trees):
        if blob["type"] == "blob" and blob["path"] != "license.tex":
            decoded_content = _blob_to_text(blob, creds)
            with open(os.path.join(save_dir, blob["path"]), "wb") as f:
                f.write(decoded_content)

    print("DONE DOWNLOADING CRING")

    jsonl_of_path(save_dir, "books/cring_train.jsonl", "books/cring_val.jsonl", 
            "books-train", "books-valid")


def napkin(creds):
    save_dir = "books/napkin"
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    resp = requests.get(
        "https://api.github.com/repos/vEnhance/napkin/git/trees/4f56c2ef5d0faf132ee14c15d96fb0f134d58bf0",
        auth=creds,
    )

    if resp.status_code != 200:
        raise AssertionError("Failed to catch napkin tree from Github API")

    trees = json.loads(resp.content.decode("utf-8"))["tree"]

    # We are assuming that we only want the files exactly two levels deep

    print("DOWNLOADING NAPKIN")
    for tree in tqdm(trees):
        if tree["type"] == "tree":
            resp = requests.get(tree["url"], auth=creds)
            blobs = json.loads(resp.content.decode("utf-8"))["tree"]
            for blob in blobs:
                if blob["type"] == "blob":
                    decoded_content = _blob_to_text(blob, creds)
                    with open(os.path.join(save_dir, blob["path"]), "wb") as f:
                        f.write(decoded_content)
    print("DONE DOWNLOADING NAPKIN")

    jsonl_of_path(save_dir, "books/napkin_train.jsonl", "books/napkin_val.jsonl", 
            "books-train", "books-valid")


def main():
    creds = ("zhangir-azerbayev", os.environ["GITHUB_TOKEN"])
    napkin(creds)
    cring(creds)
    stacks(creds)
    mizar(creds)
    afp(testing=False)
    setmm(creds)
    trench()
    hott(creds)
    stein(creds)
    coq(creds)
    lean(creds)
    hol()
    cam()


if __name__ == "__main__":
    main()

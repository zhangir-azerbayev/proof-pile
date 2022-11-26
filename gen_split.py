import os 
import random 
import json

random.seed(20)

def _get_filepaths(path): 
    filepaths = []
    for f in os.listdir(path): 
        f_path = os.path.join(path, f)
        if os.path.isfile(f_path): 
            filepaths.append(os.path.normpath(f_path))
        elif os.path.isdir(f_path): 
            filepaths += _get_filepaths(f_path)

    return filepaths

def get_split(path, train_split: float, must_be_in_train):
    filepaths = _get_filepaths(path)
    random.shuffle(filepaths)

    boundary = int(train_split * len(filepaths))

    train_paths = filepaths[:boundary]
    valid_paths = filepaths[boundary:]

    print("TRAIN SPLIT (number in train, number in val): ", len(train_paths), len(valid_paths))

    for path in must_be_in_train: 
        normed_path = os.path.normpath(path)
        assert normed_path in train_paths or normed_path in valid_paths, f"{normed_path} not in paths"
        if normed_path in valid_paths: 
            print(f"MOVING {path} to validation set")
            valid_paths.remove(path)
            train_paths.append(path)

    return train_paths, valid_paths

def arxiv_split(): 
    train_paths = []
    val_paths = []
    for f in os.listdir("arxiv"): 
        if f[-3:] == ".gz": 
            f_path = os.path.join("./arxiv", f)
            # validation set is june of years divisible by 4
            if int(f[1])%4==0 and int(f[3])==6: 
                val_paths.append(f_path)
            else: 
                train_paths.append(f_path)

    return train_paths, val_paths


def main(): 
    train_rate = 0.95
    splits = {}

    args = [
            ("books", ["books/stein/stein.tex", "books/trench/TRENCH_REAL_ANALYSIS.tex"]), 
            ("formal", ["formal/setmm/set.mm"]), 
           ]

    for subdir, must_be_in_train in args: 
        print(subdir, must_be_in_train)
        train, valid = get_split(subdir, train_rate, must_be_in_train)
        splits[subdir + "-train"] = train
        splits[subdir + "-valid"] = valid 

    train, valid = arxiv_split()
    splits["arxiv-train"] = train
    splits["arxiv-valid"] = valid
    print("arxiv", len(train), len(valid))

    with open("splits.json", "w") as f: 
        f.write(json.dumps(splits, indent=4))


if __name__=="__main__": 
    main()

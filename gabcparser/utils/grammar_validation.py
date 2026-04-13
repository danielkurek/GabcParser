import lark
import csv
import argparse
from multiprocessing import Pool
import tqdm
from .. import grammars
from .. import GabcParser
from datasets import load_dataset

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="Print lines that do not conform to specified grammar")
    parser.add_argument("-s", "--skip", type=int, default=1, help="Skip first n lines of the csv input file (default is 1 -> skip header)")
    parser.add_argument("-t", "--threads", type=int, default=None, help="Process file in multiple threads")
    parser.add_argument("--stop", action="store_true", help="Stop on first error (works only in single threaded mode")
    parser.add_argument("--transcript_column", type=str, default="transcription", help="Transcription column name")
    parser.add_argument("grammar", choices=grammars.supported_grammars, help="GABC grammar variation")
    parser.add_argument("dataset", help="HuggingFace dataset name")

def csv_reader(file, skip_lines):
    with open(file) as f:
        reader = csv.reader(f, delimiter=",")
        skip = skip_lines
        for row in reader:
            if skip > 0:
                skip -= 1
                continue
            yield row

def worker_init(grammar):
    global lark_parser
    lark_parser = GabcParser.load_parser(grammar)

def process_row(row):
    global lark_parser
    try:
        lark_parser.parse(row[1])
    except lark.exceptions.UnexpectedCharacters as err:
        error_part = row[1][max(0, err.column-20):min(len(row[1]), err.column+20)]
        return f"{row[0]},{row[1]}\nchar={err.char} ({ord(err.char)=}) col={err.column} -->{error_part}"

def main(args: argparse.Namespace):
    gabc_parser = GabcParser.load_parser(args.grammar)
    dataset = load_dataset(args.dataset)
    if args.threads is None:
        for split in dataset.keys():
            total_samples = len(dataset[split][args.transcript_column])
            for i,text in tqdm.tqdm(enumerate(dataset[split][args.transcript_column]), desc=split, total=total_samples):
                try:
                    gabc_parser.parse(text)
                except lark.exceptions.UnexpectedCharacters as err:
                    error_part = text[max(0, err.column-20):min(len(text), err.column+20)]
                    print(f"{split},{i},{text}\nchar={err.char} ({ord(err.char)=}) col={err.column} -->{error_part}")
                    if args.stop:
                        raise
    else:
        pool = Pool(args.threads, initializer=worker_init, initargs=(args.grammar,))
        for split in dataset.keys():
            total_samples = len(dataset[split][args.transcript_column])
            for result in tqdm.tqdm(pool.imap(process_row, enumerate(dataset[split][args.transcript_column]), 20), desc=split, total=total_samples):
                if result is not None:
                    print(f"{split},{result}")

        
if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
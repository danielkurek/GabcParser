from lark import Lark
import lark
import csv
import argparse
from multiprocessing import Pool
import tqdm
from .. import grammars
from .. import GabcParser

parser = argparse.ArgumentParser(prog="Print lines that do not conform to specified grammar")
parser.add_argument("-s", "--skip", type=int, default=1, help="Skip first n lines of the csv input file (skip header)")
parser.add_argument("-t", "--threads", type=int, default=None, help="Process file in multiple threads")
parser.add_argument("--stop", action="store_true", help="Stop on first error (works only in single threaded mode")
parser.add_argument("grammar", choices=grammars.supported_grammars, help="GABC grammar variation")
parser.add_argument("csv_input", help="CSV input file to validate (expected format: ID,TEXT)")

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
        return f"{row[0]},{row[1]}\nchar={err.char} ({ord(err.char)=}) col={err.column}"

def main(args: argparse.Namespace):
    gabc_parser = GabcParser.load_parser(args.grammar)
    if args.threads is None:
        for row in csv_reader(args.csv_input, args.skip):
            try:
                gabc_parser.parse(row[1])
            except lark.exceptions.UnexpectedCharacters as err:
                print(f"{row[0]},{row[1]}\nchar={err.char} ({ord(err.char)=}) col={err.column}")
                if args.stop:
                    raise
    else:
        pool = Pool(args.threads, initializer=worker_init, initargs=(args.grammar,))
        total_lines = None
        with open(args.csv_input, "rb") as f:
            total_lines = sum(1 for _ in f)
        for result in tqdm.tqdm(pool.imap(process_row, csv_reader(args.csv_input, args.skip), 20), total=total_lines):
            if result is not None:
                print(result)

        
if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
from lark import Lark
import lark
import csv
import argparse

parser = argparse.ArgumentParser(prog="Print lines that do not conform to specified grammar")
parser.add_argument("-s", "--skip", type=int, default=1, help="Skip first n lines of the csv input file (skip header)")
parser.add_argument("grammar", help="Lark grammar file path")
parser.add_argument("csv_input", help="CSV input file to validate (expected format: ID,TEXT)")

def main(args: argparse.Namespace):
    gabc_parser = Lark.open(args.grammar, debug=True)

    with open(args.csv_input) as f:
        reader = csv.reader(f, delimiter=",")
        skip_lines = args.skip
        for row in reader:
            if skip_lines > 0:
                skip_lines -= 1
                continue
            try:
                gabc_parser.parse(row[1])
            except lark.exceptions.UnexpectedCharacters as err:
                print(f"{row[0]},{row[1]}\nchar={err.char} ({ord(err.char)=}) col={err.column}")
                # raise

if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
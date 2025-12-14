from datasets import load_dataset
import argparse
from PIL import Image
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(prog="Hugging face dataset show picture")
parser.add_argument("-s", "--split", default="train", help="input files (templates)")
parser.add_argument("dataset", help="Dataset name (from hugging face)")
parser.add_argument("column", help="Column name")
parser.add_argument("row", type=int, help="Row number")


def main(args: argparse.Namespace):
    ds = load_dataset(args.dataset)
    if args.split not in ds.keys():
        raise ValueError(f"Split {args.split} is not in {args.dataset}")
    if args.column not in ds[args.split][args.row]:
        raise ValueError(f"Column {args.column} is not in {args.dataset}")
    img = ds[args.split][args.row][args.column]
    if not isinstance(img, Image.Image):
        raise ValueError(f"Given data in column {args.column} is not an image")
    plt.imshow(img)
    plt.show()



if __name__ == "__main__":
    args = parser.parse_args()
    main(args)

        
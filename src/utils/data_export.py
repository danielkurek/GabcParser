from datasets import load_dataset
from pathlib import Path
import csv

def export_dataset(ds, export_dir: Path, column: str):
    export_dir.mkdir(parents=True, exist_ok=True)
    for split in ds.keys():
        with open(export_dir / f"{split}.csv", "w") as f:
            writer = csv.writer(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(["index", column])
            for i in range(len(ds[split])):
                writer.writerow([i, ds[split][i][column].strip()])
        

datasets = [
    "PRAIG/GregoSynth_staffLevel",
    "PRAIG/Einsiedeln_staffLevel",
    "PRAIG/Salzinnes_staffLevel",
    "PRAIG/Solesmes_staffLevel"
    ]

data_dir = Path("data")

for dataset in datasets:
    ds_dir = data_dir / dataset.replace("/", "-")
    ds = load_dataset(dataset)
    export_dataset(ds, ds_dir, column="transcription")
        
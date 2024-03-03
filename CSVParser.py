from BlkEntry import BlkEntry
from pathlib import Path
from tqdm import tqdm
import csv
import subprocess


def parse_trace_lines(trace_lines):
    traces = []
    tokens = None

    for line in tqdm(trace_lines.splitlines()):
        try:
            if "Input file" in line:
                continue
            if line.startswith("CPU"):
                break

            trace, tokens = BlkEntry.parse_tokens(line.strip())
            traces.append(trace)

        except Exception:
            print(f"Parse Error (Unexpected Format):\n Line: {line}\nTokens: {tokens}\n")
            exit(1)

    return traces


def write_csv(output_file, traces):
    headers = [
        "major",
        "minor",
        "cpu",
        "seq",
        "time",
        "pid",
        "action",
        "rwbs",
        "sector",
        "blocks",
    ]

    with open(output_file, "w") as file:
        writer = csv.DictWriter(file, headers)
        writer.writeheader()
        print("Start csv writing...\n")
        for trace in tqdm(traces):
            writer.writerow(dict(zip(headers, trace)))


def traces_to_csv(g):
    input_dir = Path(g.input_dir)
    if not input_dir.exists():
        print(f"Directory {g.input_dir} doesn't exist!")
        exit(1)

    output_file = Path(g.output_file)
    output_file.parent.mkdir(exist_ok=True, parents=True)

    print("Start blkparse ...\n")
    log_file_name = input_dir / "blkparse-tmp-log.txt"

    process = subprocess.run(["blkparse", "-D", str(input_dir), "-i", g.parsefile, "-o", log_file_name], stdout=subprocess.PIPE,)
    if process.returncode == 0:
        print("blkparse Done\n")
        print("Start blkparse output parsing ...\n")
        traces = parse_trace_lines(Path(log_file_name).read_text())
        print(f"{len(traces)} trace items were parsed")
        Path(log_file_name).unlink()
    else:
        Path(log_file_name).unlink()
        process.check_returncode()

    write_csv(output_file, traces)
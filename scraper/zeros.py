import csv
from pathlib import Path

# maeve andersen
# 19 january 2024
# appends leading zeros to zips (dumb band-aid, fix this plz future me)
file_path = "chapter_zips.csv"
output_rows = []

with Path(file_path).open() as file:
    reader = csv.DictReader(file)
    for row in reader:
        row["zip"] = row["zip"].zfill(5)
        output_rows.append(row)

with Path(file_path).open(mode="w", newline="") as file:
    fieldnames = ["zip", "chapter"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(output_rows)

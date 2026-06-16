import json

with open(r"C:\Users\1337\.local\share\mimocode\tool-output\tool_ecb8e0642001dopAPPBbN5VsHN", "r") as f:
    data = json.load(f)

free = [m["id"] for m in data["data"] if ":free" in m["id"]]
for m in sorted(free):
    print(m)
print(f"\nTotal: {len(free)}")
input("\nEnter to close...")

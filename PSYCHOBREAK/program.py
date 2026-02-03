import subprocess

with open("random.dic", "r") as f:
    for line in f:
        key = line.strip()  # Removes \n and extra spaces
        print(key)
        subprocess.run(["./program", key])


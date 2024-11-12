import pandas as pd
import argparse

def read_tasks_from_md():
    task_data = []
    lines = open("productivity.md", "r").readlines()
    reset = True
    task_name = None

    for line in lines:
        if reset:
            task_name = line[2:-1]
            reset = False
            continue

        if line == "\n":
            reset = True
            continue

        task_data.append({
            "date": pd.to_datetime("today").strftime("%Y/%m/%d"),
            "task": task_name,
            "subtask": line[7:-1],
            "day_block": None,
            "time_spent": 0,
            "event": "addition",
            "completed": line[5] != " "})

    return pd.DataFrame(task_data)

def write_tasks_to_md():
    file = open("productivity.md", "w")
    task_data = pd.read_csv("productivity.csv", index_col=False)
    tasks = task_data.groupby(["task", "subtask"]).agg({
            "event": "last",
            "completed": "last"}).reset_index()
    tasks = tasks[tasks["event"] != "removal"]
    for task in tasks["task"].unique():
        file.write("- " + task + "\n")
        for subtask in tasks[tasks["task"] == task].index:
            file.write("  - [{}] ".format("X" if tasks.iloc[subtask]["completed"] else " ") + tasks.iloc[subtask]["subtask"] + "\n")
        file.write("\n")
    file.close()

write_tasks_to_md()
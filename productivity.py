import pandas as pd
import inquirer
import argparse
from functools import reduce
from parser import write_tasks_to_md

def get_subtask_menu(task_data, task):
    subtasks = task_data[task_data["task"] == task].groupby("subtask").agg({
            "date": "last",
            "time_spent": "sum",
            "event": "last",
            "completed": "last"}).reset_index()
    subtasks = subtasks[subtasks["event"] != "removal"]
    subtasks["string"] = subtasks.apply(lambda row: "[{}] {} | {} minutes spent | Latest update: {} | Latest action: {}".format(
        "X" if row["completed"] else " ",
        row["subtask"],
        row["time_spent"],
        row["date"],
        row["event"]
    ), axis=1)

    return reduce(lambda x, y: x | y, subtasks[["string", "subtask"]].apply(lambda row: {row["string"]: row["subtask"]}, axis=1).tolist())

def get_daily_summary(task_data, date):
    subtasks = task_data[task_data["date"] == date].agg({
        "time_spent": "sum",
        "day_block": "count",
        "completed": "count"})
    print(subtasks)
    print("*****Date Summary*****")
    print("Date minutes completed:", subtasks["time_spent"])
    print("Date blocks worked:", subtasks["day_block"])
    print("Date tasks completed:", subtasks["completed"])
    print("***********************")
    print()
def get_full_summary(task_data):
    subtasks = task_data.agg({
        "time_spent": "sum",
        "day_block": "count",
        "completed": "count"})
    print("*****Full Summary*****")
    print("Total minutes completed:", subtasks["time_spent"])
    print("Total blocks worked:", subtasks["day_block"])
    print("Total tasks completed:", subtasks["completed"])
    print("**********************")
    print()

def main():
    tasks = pd.read_csv("productivity.csv", index_col=False)

    while True:
        task = inquirer.prompt([inquirer.List(
            "task",
            message="Select task",
            choices=tasks["task"].unique().tolist() + ["+ Add New Task", "% View Date Summary", "$ View Full Summary", "# Write All to Markdown"],
        )]) 

        if task["task"] == "% View Date Summary":
            dates = tasks[tasks["date"] != pd.to_datetime("today").strftime("%Y/%m/%d")]["date"].unique().tolist()
            date = inquirer.prompt([inquirer.List(
                "date",
                message="Select date",
                choices=["today"] + dates,
            )]) 
            if date["date"] == "today":
                date["date"] = pd.to_datetime("today").strftime("%Y/%m/%d")
            
            get_daily_summary(tasks, date["date"])
            continue
        
        if task["task"] == "$ View Full Summary":
            get_full_summary(tasks)
            continue

        if task["task"] == "# Write All to Markdown":
            write_tasks_to_md()
            print("Markdown file productivity.md updated.")
            continue

        if task["task"] == "+ Add New Task":
            task["task"] = input("Enter task name: ")
            print("New empty task '{}' created.".format(task["task"]))
            task["subtask"] = "+ Add New Subtask"
            
            
        else:
            subtasks = get_subtask_menu(tasks, task["task"])
            task["subtask"] = inquirer.prompt([inquirer.List(
                "subtask",
                message="Select subtask",
                choices=list(subtasks.keys()) + ["+ Add New Subtask", "- Remove this task", "<- Return to task select"], # tasks[tasks["task"] == task["task"]]["subtask"].unique().tolist()
            )])["subtask"] 
            
            if task["subtask"] == "<- Return to task select":
                continue

        task = {
            "date": pd.to_datetime("today").strftime("%Y/%m/%d"),
            "task": task["task"],
            "subtask": task["subtask"],
            "day_block": None,
            "time_spent": 0,
            "event": "addition",
            "completed": False}

        if task["subtask"] == "+ Add New Subtask":
            task["subtask"] = input("Creating a subtask for the newly created task. Enter subtask name: ")
            print("New subtask '{}' created under '{}' task.".format(task["subtask"], task["task"]))
            tasks = pd.concat([tasks, pd.DataFrame({k:[v] for k,v in task.items()})])

        else:
            task["subtask"] = subtasks[task["subtask"]]
                

        actions = ["[X] Complete task", "+ Add work towards task", "- Remove this task", "<- Return to task select"]
        action = inquirer.prompt([inquirer.List(
                "action",
                message="Select action",
                choices=actions,
            )])["action"]
            
        if action == "<- Return to task select":
            continue

        if action == "[X] Complete task":
            action = inquirer.prompt([inquirer.List(
                "action",
                message="Would you like to add work towards this subtask before completing it?",
                choices=["Yes", "No"],
            )])["action"]

            if action == "Yes":
                response = inquirer.prompt([inquirer.List(
                    "day_block",
                    message="Which day block is the work done towards this task",
                    choices=list(range(1, 9)) + ["extra"],
                ), inquirer.List(
                    "time_spent",
                    message="How much time is spent on this action?",
                    choices=list(range(15, 90, 15)),
                ),])

                task["day_block"] = response["day_block"]
                task["time_spent"] = response["time_spent"]
                task["event"] = "progress"

                tasks = pd.concat([tasks, pd.DataFrame({k:[v] for k,v in task.items()})])
                print("Progress updated for subtask '{}' from task '{}'.".format(task["task"], task["subtask"]))
            
            task["time_spent"] = 0
            task["day_block"] = None
            task["event"] = "completion"
            task["completed"] = True
            tasks = pd.concat([tasks, pd.DataFrame({k:[v] for k,v in task.items()})])
            print("Subtask '{}' from task '{}' marked as complete.".format(task["task"], task["subtask"]))

        if action == "+ Add work towards task":
            response = inquirer.prompt([inquirer.List(
                "day_block",
                message="Which day block is the work done towards this task",
                choices=list(range(1, 9)) + ["extra"],
            ), inquirer.List(
                "time_spent",
                message="How much time is spent on this action?",
                choices=list(range(15, 90, 15)),
            ),])

            task["day_block"] = response["day_block"]
            task["time_spent"] = response["time_spent"]
            task["event"] = "progress"

            tasks = pd.concat([tasks, pd.DataFrame({k:[v] for k,v in task.items()})])
            print("Progress updated for subtask '{}' from task '{}'.".format(task["task"], task["subtask"]))

        if action == "- Remove this task":
            action = inquirer.prompt([inquirer.List(
                "action",
                message="Are you sure you want to remove this task?",
                choices=["Yes", "No"],
            )])["action"]

            if action == "Yes":
                task["event"] = "removal"
                tasks = pd.concat([tasks, pd.DataFrame({k:[v] for k,v in task.items()})])
            
        tasks.to_csv("productivity.csv", index=False)
        print("Subtask '{}' from task '{}' removed.".format(task["task"], task["subtask"]))

if __name__ == "__main__":
    main()

    

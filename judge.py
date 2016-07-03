#!/usr/bin/env python3
import os
import sys
import time
import judgeio

def execute():
    pass


if __name__ == "__main__":
    print("=====start=====")
    if(os.getuid() != 0):
        print("This program need root! Do you want to run it as root?(Y/N)")
        x = input().lower()
        if x == "y":
            os.execv("/usr/bin/sudo", ("sudo", "-E", "python3", __file__,))
        else:
            sys.exit(0)
    while True:
        submission_id = judgeio.get_submission_id()
        if submission_id is None:
            time.sleep(0.5)
            continue
        print("Get: ", submission_id)



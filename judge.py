#!/usr/bin/env python3
import os
import sys
import time

def execute():
    pass

def get_submission():
    pass

def get_testdata():
    pass

def get_verdict():
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
        time.sleep(0.5)
        print("Hey")


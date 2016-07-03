#!/usr/bin/env python3
import os
import sys
import time
import judgeio

def execute():
    pass

def judge():
    submission_id = judgeio.get_submission_id()
    if submission_id is None:
        time.sleep(0.5)
        return
    print("Get: ", submission_id)
    submission_data = judgeio.get_submission(submission_id)
    judgeio.get_submission_file(submission_data)
    print(submission_data)
    problem_data = judgeio.get_problem(submission_data['problem_id'])
    print(problem_data)
    verdict = problem_data['verdict']
    testdata = problem_data['testdata']
    print(verdict)
    print(testdata)
    judgeio.get_testdata(problem_data['id'], testdata)




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
        judge()
        sys.exit()

import requests
import json
import config
import os

def get_submission_id():
    payload = {
        "token": config.token
    }
    url = "%s/api/judge/"%(config.base_url)
    res = requests.get(url, data=payload)
    try:
        data = json.loads(res.text)
        return int(data['msg']['submission_id'])
    except:
        return None

def get_submission(submission_id):
    url = "%s/api/submissions/%s/"%(config.base_url, submission_id)
    payload = {
        "token": config.token
    }
    res = requests.get(url, data=payload)
    try:
        data = json.loads(res.text)['msg']
        return data
    except:
        return None

def get_submission_file(submission_data):
    url = "%s/api/submissions/%s/file/"%(config.base_url, submission_data['id'])
    payload = {
        "token": config.token
    }
    res = requests.get(url, data=payload)
    with open(submission_data['file_name'], "wb") as f:
        f.write(res.text.encode())

def get_testdatum(problem_id, testdatum):
    payload = {
        "token": config.token
    }
    try:
        os.makedirs('./testdata/%s'%(testdatum['id']))
    except:
        pass
    for x in ["input", "output"]:
        url = "%s/api/problems/%s/testdata/%d/input/"%(config.base_url, problem_id, testdatum['id'])
        res = requests.get(url, data=payload)

        with open('testdata/%s/%s'%(testdatum['id'], x), "wb") as f:
            f.write(res.text.encode())


def get_testdata(problem_id, testdata):
    for testdatum in testdata:
        get_testdatum(problem_id, testdatum)

def get_verdict():
    pass

def get_problem(problem_id):
    url = "%s/api/problems/%s/"%(config.base_url, problem_id)
    payload = {
        "token": config.token
    }
    res = requests.get(url, data=payload)
    try:
        data = json.loads(res.text)['msg']
        return data
    except:
        return None
    pass

def get_execute_types():
    pass

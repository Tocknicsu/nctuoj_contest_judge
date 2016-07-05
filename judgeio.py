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
    folder = "%s/submissions/%s"%(config.DATA_ROOT, submission_data['id'])
    try:
        os.makedirs(folder)
    except:
        pass
    res = requests.get(url, data=payload)
    with open("%s/%s"%(folder, submission_data['file_name']), "wb") as f:
        f.write(res.text.encode())

def get_testdatum(problem_id, testdatum):
    payload = {
        "token": config.token
    }
    folder = "%s/testdata/%s"%(config.DATA_ROOT, testdatum['id'])
    try:
        os.makedirs(folder)
    except:
        pass
    for x in ["input", "output"]:
        url = "%s/api/problems/%s/testdata/%d/%s/"%(config.base_url, problem_id, testdatum['id'], x)
        res = requests.get(url, data=payload)

        with open('%s/%s'%(folder, x), "wb") as f:
            f.write(res.text.encode())


def get_testdata(problem_id, testdata):
    for testdatum in testdata:
        get_testdatum(problem_id, testdatum)

def get_verdict_file(verdict_data):
    url = "%s/api/problems/%s/verdict/file/"%(config.base_url, verdict_data['id'])
    payload = {
        "token": config.token
    }
    folder = "%s/verdicts/%s"%(config.DATA_ROOT, verdict_data['id'])
    try:
        os.makedirs(folder)
    except:
        pass
    res = requests.get(url, data=payload)
    with open("%s/%s"%(folder, verdict_data['file_name']), "wb") as f:
        f.write(res.text.encode())

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

def get_execute_types(execute_type_id):
    url = "%s/api/executes/%s/"%(config.base_url, execute_type_id)
    payload = {
        "token": config.token
    }
    res = requests.get(url, data=payload)
    try:
        data = json.loads(res.text)['msg']
        return data
    except:
        return None

def get_languages():
    url = "%s/api/languages/"%(config.base_url)
    payload = {
        "token": config.token
    }
    res = requests.get(url, data=payload)
    try:
        data = json.loads(res.text)['msg']
        return data
    except:
        return None


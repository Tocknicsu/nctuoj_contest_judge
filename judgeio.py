import requests
import json
import config

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

def get_submission():
    pass

def get_testdata():
    pass

def get_verdict():
    pass


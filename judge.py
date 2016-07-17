#!/usr/bin/env python3
import os
import sys
import time
import judgeio
import config
from isolate import Sandbox
import subprocess as sp

class Judge():
    def prepare_sandbox(self):
        self.sandbox = Sandbox(os.getpid(), './isolate')
        self.sandbox.folder = "/tmp/box/%s/box/"%(os.getpid())
        self.sandbox.init_box()
        self.verdict_sandbox = Sandbox(os.getpid() + 65536, './isolate')
        self.verdict_sandbox.folder = "/tmp/box/%s/box/"%(os.getpid()+65536)
        self.verdict_sandbox.init_box()

    def clear_sandbox(self):
        if self.sandbox is not None:
            self.sandbox.delete_box()
        if self.verdict_sandbox is not None:
            self.verdict_sandbox.delete_box()


    def cmd_replace(self, cmd, param):
        for idx, c in enumerate(cmd):
            if "file_name" in param:
                c = c.replace("__FILE__", param['file_name'])
                c = c.replace("__FILE_EXTENSION__", param['file_name'].split(".")[-1])
                c = c.replace("__MAIN_FILE__", ('.').join(param['file_name'].split(".")[:-1]))
            if "memory_limit" in param:
                c = c.replace("__MEMORY_LIMIT__", str(param['memory_limit']))
            cmd[idx] = c
        return cmd

    def read_meta(self, file_path):
        res = {
            "status": "AC",
            "time": 0,
            "memory": 0,
            "exitcode": 0,
        }
        try: f = open(file_path).read().splitlines()
        except:
            res['status'] = 'SE'
            return res
        for x in f:
            x = x.split(":")
            if x[0] == "status":
                res['status'] = x[1]
            elif x[0] == "time":
                res["time"] = int(1000*float(x[1]))
            elif x[0] == "max-rss":
                res["memory"] = int(x[1])
            elif x[0] == "exitcode":
                res['exitcode'] = int(x[1])
            else:
                res[x[0]] = x[1]
        if res['status'] == "TO":
            res['status'] = "TLE"
            res['time'] = max(int(1000*float(res['time-wall'])), res['time'])
        if res['status'] == "SG":
            res['status'] = "RE" 
        return res

    def compile(self, sandbox, data):
        sandbox.options = {
            "proc_limit": 4,
            "meta": "%s/meta"%(sandbox.folder),
            "output": "compile_msg",
            "errput": "compile_msg",
            "mem_limit": 262144 << 2,
            "time_limit": 3,
        }
        ### special option for each lang
        if data['lang'] == "Java":
            self.sandbox.options['mem_limit'] = 0
            self.sandbox.options['proc_limit'] = 16
        sandbox.set_options(**self.sandbox.options)
        res = {
            "status": "AC",
            "exitcode": 0,
        }
        for x in data['commands'][:-1]:
            command = x['command']
            run_cmd = [x for x in command.split(' ')]
            run_cmd = self.cmd_replace(run_cmd, {
                "file_name": data['file_name'],
                "memory_limit": 262144,
            })
            sandbox.exec_box(["/usr/bin/env"] + run_cmd)
            res = self.read_meta(self.sandbox.options['meta'])
            if res['status'] != "AC":
                return res 
        return res

    def exec(self, testdatum, submission_execute, submission_data):
        # sp.call("cp '%s/testdata/%s/input' '%s'"%(config.DATA_ROOT, testdatum['id'], self.sandbox.folder), shell=True)
        sp.call(['cp', os.path.join(config.DATA_ROOT, 'testdata', str(testdatum['id']), 'input'), self.sandbox.folder])
        self.sandbox.options['proc_limit'] = 4
        self.sandbox.options['input'] = "input"
        self.sandbox.options['time_limit'] = testdatum['time_limit'] / 1000
        self.sandbox.options['mem_limit'] = testdatum['memory_limit']
        self.sandbox.options['fsize_limit'] = testdatum['output_limit'] 
        self.sandbox.options['output'] = "output"
        self.sandbox.options["errput"] = "errput"
        if submission_execute['lang'] == "Java":
            self.sandbox.options['mem_limit'] = 0
            self.sandbox.options['proc_limit'] = 16
        self.sandbox.set_options(**self.sandbox.options)
        command = submission_execute['commands'][-1]['command']
        run_cmd = command.split(' ')
        run_cmd = self.cmd_replace(run_cmd, {
            "file_name": submission_data['file_name'],
            "memory_limit": testdatum['memory_limit'],
        })
        self.sandbox.exec_box(["/usr/bin/env"] + run_cmd)
        res = self.read_meta(self.sandbox.options['meta'])
        if res['status'] == "AC":
            if res['memory'] > testdatum['memory_limit']:
                res['status'] = "MLE"
        return res

    def verdict(self, verdict_execute, file_a, file_b):
        self.verdict_sandbox.options = {
            "proc_limit": 4,
            "meta": "%s/meta"%(self.verdict_sandbox.folder),
            "mem_limit": 262144,
            "time_limit": 3,
            "output": "verdict",
            "errput": "verdict_error",
        }
        command = verdict_execute['commands'][-1]['command']
        run_cmd = command.split(' ')
        run_cmd = self.cmd_replace(run_cmd, {
            "file_name": verdict_execute['file_name'],
            "memory_limit": 262144,
        })
        if verdict_execute['lang'] == "Java":
            self.sandbox.options['mem_limit'] = 0
            self.sandbox.options['proc_limit'] = 16

        self.verdict_sandbox.set_options(**self.verdict_sandbox.options)

        sp.call(['cp', file_a, os.path.join(self.verdict_sandbox.folder, 'file_a')])
        sp.call(['cp', file_b, os.path.join(self.verdict_sandbox.folder, 'file_b')])
        self.verdict_sandbox.exec_box(["/usr/bin/env"] + run_cmd + ["file_a", "file_b"])
        res = self.read_meta(self.verdict_sandbox.options['meta'])
        if res['status'] != "AC":
            return ("SE", "Verdict Execute Result:"+str(res['status']))
        f = open("%s/verdict"%(self.verdict_sandbox.folder), "r")
        x = f.read().split(" ")
        if len(x) != 2:
            return ("SE", "Verdict result wrong, it should be '[AC|WA]' 'score_rate'")
        if x[0] != "AC" and x[0] != "WA":
            return ("SE", "Verdict result wrong, it should be '[AC|WA]' 'score_rate'")
        try:
            return (x[0], float(x[1]))
        except:
            return ("SE", "Verdict result wrong, it should be '[AC|WA]' 'score_rate'")

    def run(self):
        submission_id = judgeio.get_submission_id()
        if submission_id is None:
            print(".", end="")
            sys.stdout.flush()
            time.sleep(1)
            return
        self.clear_sandbox()
        self.prepare_sandbox()
        print()
        print("Get: ", submission_id)

        ### get language
        languages = { x['id']: x['name'] for x in judgeio.get_languages()}
        verdict_types = { x['abbreviation']: x['id'] for x in judgeio.get_verdict_type()}

        ### get submission data
        submission_data = judgeio.get_submission(submission_id)
        if submission_data is None:
            return
        submission_file = judgeio.get_submission_file(submission_data)
        if submission_file is None:
            return
        submission_execute = judgeio.get_execute_types(submission_data['execute_type_id'])
        if submission_execute is None:
            return
        submission_execute['lang'] = languages[submission_execute['language_id']]
        submission_execute['file_name'] = submission_data['file_name']
        ### get problem data
        problem_data = judgeio.get_problem(submission_data['problem_id'])
        if problem_data is None:
            return
        ### get testdata
        testdata = problem_data['testdata']
        if len(testdata) == 0:
            post_res = judgeio.post_submission(submission_id)
            return

        testdata_result = judgeio.get_testdata(problem_data['id'], testdata)
        if testdata_result is None:
            return 
        ### get verdict
        verdict = problem_data['verdict']
        verdict_file = judgeio.get_verdict_file(verdict)
        if verdict_file is None:
            return

        verdict_execute = judgeio.get_execute_types(verdict['execute_type_id'])
        if verdict_execute is None:
            return
        verdict_execute['lang'] = languages[verdict_execute['language_id']]
        verdict_execute['file_name'] = verdict['file_name']

        ### submission compile
        # sp.call("cp '%s/submissions/%s/%s' '%s'"%(config.DATA_ROOT, submission_data['id'], submission_data['file_name'], self.sandbox.folder), shell=True)
        sp.call(['cp', os.path.join(config.DATA_ROOT, 'submissions', str(submission_data['id']), submission_data['file_name']), self.sandbox.folder])
        compile_res = self.compile(self.sandbox, submission_execute)
        if compile_res['status'] != "AC":
            ### submission CE
            post_submission_testdata = {
                "submission_id": submission_data['id'],
                "testdata_id": testdata[0]['id'],
                "verdict_id": verdict_types["CE"],
                "note": open("%s/compile_msg"%(self.sandbox.folder), "r").read(),
            }
            post_res = judgeio.post_submission_testdata(post_submission_testdata)
            if post_res is None:
                return
            post_res = judgeio.post_submission(submission_id)
            if post_res is None:
                return
            return


        ### verdict compile
        # sp.call("cp '%s/verdicts/%s/%s' '%s'"%(config.DATA_ROOT, verdict['id'], verdict['file_name'], self.verdict_sandbox.folder), shell=True)
        sp.call(['cp', os.path.join(config.DATA_ROOT, 'verdicts', str(verdict['id']), verdict['file_name']), self.verdict_sandbox.folder])
        compile_res = self.compile(self.verdict_sandbox, verdict_execute)
        if compile_res['status'] != "AC":
            ### verdict CE => SE
            post_submission_testdata = {
                "submission_id": submission_data['id'],
                "testdata_id": testdata[0]['id'],
                "verdict_id": verdict_types["SE"],
                "note": "Cannot compile verdict\n" + open("%s/compile_msg"%(self.verdict_sandbox.folder), "r").read(),
            }
            post_res = judgeio.post_submission_testdata(post_submission_testdata)
            if post_res is None:
                return
            post_res = judgeio.post_submission(submission_id)
            if post_res is None:
                return
            return

        for testdatum in testdata:
            exec_res = self.exec(testdatum, submission_execute, submission_data)
            ### if execute without any wrong, run verdict
            if exec_res['status'] == "AC":
                file_a = "%s/testdata/%s/output"%(config.DATA_ROOT, testdatum['id'])
                file_b = "%s/output"%(self.sandbox.folder)
                verdict_res = self.verdict(verdict_execute, file_a, file_b)
                ### if verdict wrong => SE
                if verdict_res[0] == "SE":
                    post_submission_testdata = {
                        "submission_id": submission_data['id'],
                        "testdata_id": testdatum['id'],
                        "verdict_id": verdict_types["SE"],
                        "note":  verdict_res[1],
                    }
                    post_res = judgeio.post_submission_testdata(post_submission_testdata)
                    if post_res is None:
                        return
                else:
                    post_submission_testdata = {
                        "submission_id": submission_data['id'],
                        "testdata_id": testdatum['id'],
                        "time_usage": exec_res['time'],
                        "memory_usage": exec_res['memory'],
                        "score": int(verdict_res[1] * testdatum['score']),
                        "verdict_id": verdict_types[verdict_res[0]],
                    }
                    ### io post submission testdata
                    post_res = judgeio.post_submission_testdata(post_submission_testdata)
                    if post_res is None:
                        return
            else:
                post_submission_testdata = {
                    "submission_id": submission_data['id'],
                    "testdata_id": testdatum['id'],
                    "verdict_id": verdict_types[exec_res['status']],
                    "time_usage": exec_res['time'],
                    "memory_usage": exec_res['memory'],
                    'score': 0,
                }
                ### io post submission testdata
                post_res = judgeio.post_submission_testdata(post_submission_testdata)
                if post_res is None:
                    return
        post_res = judgeio.post_submission(submission_id)
        if post_res is None:
            return

if __name__ == "__main__":
    print("=====start=====")
    if(os.getuid() != 0):
        print("This program need root! Do you want to run it as root?(Y/N)")
        x = input().lower()
        if x == "y":
            os.execv("/usr/bin/sudo", ("sudo", "-E", "python3", __file__,))
        else:
            sys.exit(0)
    judge = Judge()
    while True:
        judge.run()

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
        self.sandbox.delete_box()
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
            "mem_limit": 262144,
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
        sp.call("cp '%s/testdata/%s/input' '%s'"%(config.DATA_ROOT, testdatum['id'], self.sandbox.folder), shell=True)
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

        sp.call("cp '%s' '%s/file_a'"%(file_a, self.verdict_sandbox.folder), shell=True)
        sp.call("cp '%s' '%s/file_b'"%(file_b, self.verdict_sandbox.folder), shell=True)
        self.verdict_sandbox.exec_box(["/usr/bin/env"] + run_cmd + ["file_a", "file_b"])
        res = self.read_meta(self.verdict_sandbox.options['meta'])
        f = open("%s/verdict"%(self.verdict_sandbox.folder), "r")
        x = f.read().split(" ")
        if len(x) != 2:
            return ("SE", 0.0)
        if x[0] != "AC" and x[0] != "WA":
            return ("SE", 0.0)
        try:
            return (x[0], float(x[1]))
        except:
            return ("SE", 0.0)

    def run(self):
        submission_id = judgeio.get_submission_id()
        if submission_id is None:
            time.sleep(0.5)
            return
        self.prepare_sandbox()
        print("Get: ", submission_id)

        ### get language
        languages = { x['id']: x['name'] for x in judgeio.get_languages()}


        ### get submission data and compile
        submission_data = judgeio.get_submission(submission_id)
        judgeio.get_submission_file(submission_data)
        submission_execute = judgeio.get_execute_types(submission_data['execute_type_id'])
        submission_execute['lang'] = languages[submission_execute['language_id']]
        submission_execute['file_name'] = submission_data['file_name']
        sp.call("cp '%s/submissions/%s/%s' '%s'"%(config.DATA_ROOT, submission_data['id'], submission_data['file_name'], self.sandbox.folder), shell=True)
        compile_res = self.compile(self.sandbox, submission_execute)
        if compile_res['status'] != "AC":
            ### CE
            ### io post submission
            self.clear_sandbox()
            return

        ### get problem data
        problem_data = judgeio.get_problem(submission_data['problem_id'])

        ### get verdict data and compile
        verdict = problem_data['verdict']
        judgeio.get_verdict_file(verdict)
        verdict_execute = judgeio.get_execute_types(verdict['execute_type_id'])
        verdict_execute['lang'] = languages[verdict_execute['language_id']]
        verdict_execute['file_name'] = verdict['file_name']
        sp.call("cp '%s/verdicts/%s/%s' '%s'"%(config.DATA_ROOT, verdict['id'], verdict['file_name'], self.verdict_sandbox.folder), shell=True)
        compile_res = self.compile(self.verdict_sandbox, verdict_execute)
        if compile_res['status'] != "AC":
            ### io post submission
            ### SE
            self.clear_sandbox()
            return

        ### get testdata
        testdata = problem_data['testdata']
        judgeio.get_testdata(problem_data['id'], testdata)
        for testdatum in testdata:
            exec_res = self.exec(testdatum, submission_execute, submission_data)
            ### if AC
            ### run verdict
            if exec_res['status'] != "AC":
                pass
            else:
                file_a = "%s/testdata/%s/output"%(config.DATA_ROOT, testdatum['id'])
                file_b = "%s/output"%(self.sandbox.folder)
                verdict_res = self.verdict(verdict_execute, file_a, file_b)
                print("===Verdict===", verdict_res)
            ### io post submission testdata







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
        sys.exit()

import os
import subprocess as sp

class Sandbox:
    class SandboxOption:
        def __init__(self):
            meta = {}
            meta['dir'] = {
                            '/var': None,
                            '/tmp': None
                        }
            meta['env'] = dict()
            meta["cgroup"] = True               #--cg
            meta["full_env"] = True             #--full-env
            meta["input"] = ''                  #--stdin
            meta["output"] = ''                 #--stdout
            meta["errput"] = ''                 #--stderr
            meta["meta"] = ''                   #--meta
            meta["mem_limit"] = 65535           #--mem
            meta['proc_limit'] = 1              #--processes
            meta['time_limit'] = 1              #--time
            meta['fsize_limit'] = 65535         #--fsize
            self._meta = meta
            self.set_env(LD_LIBRARY_PATH='/usr/local/lib/')
            self.set_env(PATH='/usr/lib/jvm/java-8-oracle/bin/')

        def set_env(self, **kwargs):
            for var in kwargs:
                kwargs[var] = '%s:%s'%(os.environ.get(var) or '', kwargs[var])
            self._meta['env'].update(kwargs)

        def set_dir(self, dirs):
            self._meta['dir'].update(dirs)

        def clear_dir(self):
            self._meta['dir'] = {
                            '/var': None,
                            '/tmp': None
                        }

        def set_options(self, **kwargs):
            self._meta.update(kwargs)

        def __getitem__(self, index):
            return self._meta[index]

    def __init__(self, box_id, isolate):
        self._isolate = isolate
        self._box_id = box_id
        self._opt = self.SandboxOption()

    def set_options(self, **kwargs):
        self._opt.set_options(**kwargs)

    def init_box(self):
        cmd = [self._isolate, '--box-id', str(self._box_id),]
        if self._opt['cgroup']: cmd += ['--cg']
        cmd += ['--init']
        sp.call(cmd)

    def delete_box(self):
        cmd = [self._isolate, '--box-id', str(self._box_id), '--cleanup']
        print(cmd)
        sp.call(cmd)

    
    def exec_box(self, exec_cmd):
        cmd = [self._isolate, '--box-id', str(self._box_id)]
        if self._opt['full_env']: cmd += ['--full-env']
        if self._opt['input']: cmd += ['--stdin=%s'%self._opt['input']]
        if self._opt['output']: cmd += ['--stdout=%s'%self._opt['output']]
        if self._opt['errput']: cmd += ['--stderr=%s'%self._opt['errput']]
        if self._opt['meta']: cmd += ['--meta=%s'%self._opt['meta']]
        if self._opt['mem_limit']: cmd += ['--mem=%s'%str(self._opt['mem_limit'])]
        if self._opt['mem_limit']: cmd += ['--cg-mem=%s'%str(self._opt['mem_limit'])]
        if self._opt['proc_limit']: cmd += ['--processes=%s'%str(self._opt['proc_limit'])]
        elif self._opt['proc_limit'] == 0: cmd += ['--processes']
        if self._opt['time_limit']: cmd += ['--time=%s'%str(self._opt['time_limit'])]
        if self._opt['time_limit']: cmd += ['--wall-time=%s'%str(self._opt['time_limit'])]
        if self._opt['fsize_limit']: cmd += ['--fsize=%s'%str(self._opt['fsize_limit'])]
        if self._opt['env']: 
            for (var, val) in self._opt['env'].items():
                cmd += ['--env', '%s=%s'%(var, val)]
        if self._opt['dir']:
            for (out, _in) in self._opt['dir'].items():
                if _in: cmd += ['--dir', '%s=%s'%(out, _in)]
                else: cmd += ['--dir', out]
        cmd += ['--extra-time', '0.20', '--stack', '0', '--run', '--']
        cmd += exec_cmd
        print("Run: ", exec_cmd)
        print("Final: ", cmd)
        #return sp.call(cmd, shell=True, env=os.environ, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
        return sp.call(cmd, env=os.environ)

        
if __name__ == "__main__":
    s = Sandbox(1, './isolate')
    s.set_options(proc_limit=100, meta='meta', mem_limit=65535*200)
    s.init_box()
    s.exec_box(["/usr/bin/env", "mkdir", "test"])
    s.exec_box(["/usr/bin/env", "ls"])
    s.exec_box(["/usr/bin/env", "cd", "test", "&&", "touch", "XD"])
    s.exec_box(["/usr/bin/env", "ls"])
    #sp.call("cp test.py /tmp/box/1/box/", shell=True)
    #s.exec_box("/usr/bin/env python3 test.py")
    #s.exec_box("./test")
    #s.exec_box("/usr/bin/env java")
    #s.exec_box("/usr/bin/env ghc")
    #s.delete_box()

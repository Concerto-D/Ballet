from subprocess import run
import sys
import os
import shutil
import threading

_ansible_call_lock = threading.Lock()
_ansible_call_id = 0

class AnsibleCallResult:
    def __init__(self, command : str, return_code : int, stdout : str = None, stderr : str = None):
        self.command = command
        self.return_code = return_code
        self.stdout = stdout
        self.stderr = stderr

def call_ansible_on_host(host, playbook, tag="all", extra_vars=None, user="root", capture_output=False, debug_printing=False) -> AnsibleCallResult:
    from json import dump, dumps
    global _ansible_call_lock
    global _ansible_call_id
    with _ansible_call_lock:
        directory = "_ansible_calls/%d"%_ansible_call_id
        _ansible_call_id += 1
    if not os.path.exists(directory):
        os.makedirs(directory)
    shutil.copy("ansible.cfg",directory)
    if extra_vars is None:
        extra_vars = {}
    with open(directory + "/extra_vars.json", "w") as extra_vars_file:
        dump(extra_vars, extra_vars_file)
    #extra_vars_string = " --extra-vars \"%s\"" % ' '.join(["%s=%s"%(key, str(value)) for key,value in extra_vars.items()])
    extra_vars_string = " --extra-vars \"@extra_vars.json\""
    if playbook[0] != '/':
        playbook = "../../" + playbook
    command = "cd %s;ansible-playbook -u %s -i %s, %s --tags \"%s\"%s" % (directory, user, host, playbook, tag, extra_vars_string)
    if debug_printing:
        sys.stderr.write("Executing command: %s (extra vars: %s)\n"%command, dumps(extra_vars))
        sys.stderr.flush()
    if sys.version_info >= (3, 7):
        completed_process = run(command, shell=True, check=False, capture_output=capture_output)
        if debug_printing:
            sys.stderr.write("Stdout:\n%s\nStderr:\n%s\n"%(completed_process.stdout,completed_process.stderr))
            sys.stderr.flush()
        return AnsibleCallResult(
            command = command,
            return_code = completed_process.returncode,
            stdout = completed_process.stdout,
            stderr = completed_process.stderr
        )
    else:
        completed_process = run(command, shell=True, check=False)
        if debug_printing:
            sys.stderr.write("Stdout:\n%s\nStderr:\n%s\n"%(completed_process.stdout,completed_process.stderr))
            sys.stderr.flush()
        return AnsibleCallResult(
            command = command,
            return_code = completed_process.returncode,
        )

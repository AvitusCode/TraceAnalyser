import Checker as check
import os, sys, subprocess, shlex


def cleanup_files(g):
    check.verbose_print(g, "Cleaning up temp files\n")
    for file in g.cleanup:
        check.debug_print(g, file)
        os.system("rm -f " + file)
    os.system("rm -f filetrace.*.txt")
    return


def run_cmd(g, cmd):
    rc  = 0
    out = ""
    check.debug_print(g, "cmd: " + cmd)
    args = shlex.split(cmd)
    
    try:
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        print("ERROR: problem with Popen")
        sys.exit(1)
    try: 
        out, error = p.communicate()
    except:
        print("ERROR: problem with Popen.communicate()")

    rc = p.returncode
    if rc == 0:
        check.debug_print(g, "rc=" + str(p.returncode))
    else:
        print('FAILED cmd: ' + cmd)
        check.trace_failed()
        
    return out.decode()


def run_sys_cmd(g, cmd):
    check.debug_print(g, "sys cmd: " + cmd)
    rc = os.system(cmd)
    if rc != 0:
        print('FAILED sys cmd: ' + cmd)
        check.trace_failed()

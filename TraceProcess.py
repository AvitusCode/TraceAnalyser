import os, sys
import Commands
import Checker as check


def trace_process(g):
    # Trace
    # Check sudo permissions
    Commands.run_sys_cmd("sudo -v &>/dev/null")
    Commands.run_sys_cmd("fdisk -l -u=sectors "+g.device+" > fdisk."+g.device_str) # Get info about block device
    Commands.run_sys_cmd("rm -f blk.out.* &>/dev/null")                            # Cleanup previous mess

    runcount = g.runtime / g.timeout
    while runcount > 0:
        time_left = runcount * g.timeout
        percent_prog = (g.runtime - time_left) * 100  / g.runtime
        check.printf( "\r%d %% done (%d seconds left)", percent_prog, time_left)
        # BEN
        sys.stdout.flush()
        cmd = "blktrace -b " + str(g.buffer_size) + " -n " + str(g.buffer_count) + " -a queue -d " + str(g.device) + " -o blk.out." + str(g.device_str) + ".0 -w " + str(g.timeout) + " &> /dev/null"
        Commands.run_sys_cmd(cmd)
        cmd = "blkparse -i blk.out." + g.device_str + ".0 -q -f " + '" %d %a %S %n\n" | grep -v cfq | gzip --fast > blk.out.' + g.device_str + ".0.blkparse.gz;"
        Commands.run_sys_cmd(cmd)
        runcount -= 1

    print("\rMapping files to block locations")
    tarball_name = g.device_str + ".tar"
    print("\rCreating tarball " + tarball_name)
    filetrace = ""
    cmd = "tar -cf " + tarball_name + " blk.out." + g.device_str + ".*.gz fdisk." + g.device_str + " " + filetrace + " &> /dev/null"
    Commands.run_sys_cmd(cmd)
    cmd = "rm -f blk.out." + g.device_str + ".*.gz; rm -f fdisk." + g.device_str + "; rm -f filetrace." + g.device_str + ".*.gz"
    Commands.run_sys_cmd(cmd)
    print("\rFINISHED tracing: " + tarball_name)
    name = os.path.basename(__file__)
    print("Please use this file with " + name + " -m post -t " + tarball_name + " to create a report")
    
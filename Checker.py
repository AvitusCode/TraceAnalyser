import os, sys, getopt, re, stat
import json


def help_func(g, argv):
    name = os.path.basename(__file__)
    print("Invalid command\n")
    print(name)
    
    for opt in argv:
        print(opt)
    
    print("\n\nUsage:")
    print(name + " -m trace -d <dev> -r <runtime> [-v] # run trace for post-processing later")
    print(name + " -m post  -f <dev.tar file>     [-v] # post-process mode")
    print(name + " -m parse -f <pasefile> # plot a specific info about the blktrace")
    print("\nCommand Line Arguments:")
    print("-d <dev>            : The device to trace (e.g. /dev/sdb).  You can run traces to multiple devices (e.g. /dev/sda and /dev/sdb)")
    print("                      at the same time, but please only run 1 trace to a single device (e.g. /dev/sdb) at a time")
    print("-r <runtime>        : Runtime (seconds) for tracing")
    print("-f <dev.tar file>   : A .tar file is created during the 'trace' phase.  Please use this file for the 'post' phase")
    print("                      You can offload this file and run the 'post' phase on another system.")
    print("-v (-x)             : (OPTIONAL) Print verbose messages.")
    sys.exit(-1)


def trace_failed():
    print("Unable to run the 'blktrace' tool required to trace all of your I/O")
    print("If you are using SLES 11 SP1, then it is likely that your default kernel is missing CONFIG_BLK_DEV_IO_TRACE")
    print("which is required to run blktrace.  This is only available in the kernel-trace version of the kernel.")
    print("kernel-trace is available on the SLES11 SP1 DVD and you simply need to install this and boot to this")
    print("kernel version in order to get this working.")
    print("If you are using a differnt distro or custom kernel, you may need to rebuild your kernel with the 'CONFIG_BLK 1f40 _DEV_IO_TRACE'")
    print("option enabled.  This should allow blktrace to function\n")
    print("ERROR: Could not run blktrace")
    sys.exit(7)


def debug_print(g, message):
    if g.debug == True:
        print(message)


def verbose_print(g, message):
    if g.verbose == True:
        print(message)


def printf(format, *args):
    sys.stdout.write(format % args)


def check_trace_prereqs(g):
    debug_print(g, "check_trace_prereqs")

    rc = os.system("which blktrace &> /dev/null")
    if rc != 0:
        print("ERROR: blktrace not installed.  Please install blktrace")
        sys.exit(1)
    else:
        debug_print(g, "which blktrace: rc=" + str(rc))

    rc = os.system("which blkparse &> /dev/null")
    if rc != 0:
        print("ERROR: blkparse not installed.  Please install blkparse")
        sys.exit(1)
    else:
        debug_print(g, "which blkparse: rc=" + str(rc))



def match_args(g, opts, argv):
    for opt, arg in opts:
        if opt ==  '-m':
            g.mode = arg
        elif opt == '-a':
            g.parseaction = arg
        elif opt == '-d':
            g.device = arg
        elif opt == '-o':
            g.output_file = arg
        elif opt == '-t':
            g.thread_mode = True
            g.selected_thread = int(arg)
        elif opt == '-f':
            g.tarfile = arg
            g.parsefile = arg
        elif opt == '-r':
            g.runtime = int(arg)
            if g.runtime < 3:
                g.runtime = 3 # Min runtime
        elif opt == '-v':
            g.verbose = True
        elif opt == '-x':
            g.verbose = True
            g.debug = True
        else:
            help_func(g, argv)



def load_config(g):
    try:
        with open('pion_config.json', 'r') as config:
            settings = json.load(config)
            g.sector_size = int(settings['sector_size'])
            g.block_size  = int(settings['block_size'])
            g.plot_mode   = settings['plot_mode']
            g.plot_format = settings['plot_format']
            g.weight = int(settings['weight'])
            g.time_period_start = float(settings["time_period_start"])
            g.time_period_end = float(settings["time_period_end"])
            g.sector_start = int(settings["sector_start"])
            g.sector_end = int(settings["sector_end"])
            g.parseaction = settings["parse_action"]
            g.parsemode = settings["parse_mode"]
            g.cut_seq = bool(settings["cut_seq"])
            g.time_cover = float(settings["time_cover"])
            g.thread_mode = bool(settings["thread_mode"])
            g.selected_thread = int(settings["selected_thread"])
            g.with_predicted = bool(settings["with_predicted"])
            g.pp_file = settings["pp_file"]

    except Exception as ex:
        print(f"Exception while reading json settings {ex=}, {type(ex)=}")


def check_args(g, argv):
    try:
        opts, _ = getopt.getopt(argv, "a:o:m:d:t:f:r:vx")
    except getopt.GetoptError as err:
        print(str(err))
        help_func(g, argv)

    # Parse arguments
    match_args(g, opts, argv)

    # Check arguments
    if g.verbose == True or g.debug == True:
        verbose_print(g, "verbose: " + str(g.verbose) + " debug: " + str(g.debug))

    match g.mode:
        case 'parse':
            verbose_print(g, "PARSE")
            load_config(g)
            if g.parsefile == '':
                help_func(g, argv)
            if g.parseaction not in ('W', 'R', 'A', 'RS'):
                help_func(g, argv)
            if g.parsemode not in ('hf', 'tlba', 'blkp', 'iobt'):
                help_func(g, argv)
            if g.time_period_start % g.time_cover != 0 or g.time_period_end % g.time_cover:
                print("The time_cover should divide the time_period_start and time_period_end range")

        case 'post':
            verbose_print(g, "POST")

            if g.tarfile == '':
                help_func(g,argv)
            match = re.search("(\S+).tar", g.tarfile)

            try:
                debug_print(g,match.group(1))
                g.device_str = match.group(1)
            except:
                print("ERROR: invalid tar file" + g.tarfile)
    
            g.fdisk_file = "fdisk." + g.device_str
            debug_print(g, "fdisk_file: " + g.fdisk_file)
            g.cleanup.append(g.fdisk_file)

        case 'trace':
            verbose_print(g, "TRACE")
            check_trace_prereqs(g)

            if g.device == '' or g.runtime == '':
                help_func(g,argv)

            debug_print(g, "Dev: " + g.device + " Runtime: " + str(g.runtime))
            match = re.search("\/dev\/(\w+-\d+)", g.device)
            try: 
                debug_print(g, match.group(1))
                g.device_str = match.group(1)
            except:
                print("Invalid Device Type: {}".format(match))
                help_func(g, argv)
            statinfo = os.stat(g.device)

            if not stat.S_ISBLK(statinfo.st_mode):
                print("Device " + g.device + " is not a block device")
                help_func(g,argv)

        case _:
            help_func(g,argv)
        
    return


def regex_find(g, pattern, input):
    output = False

    if g.verbose == True or g.debug == True:
        print("PATTERN: ", pattern)

    for line in input.split("\n"):
        if g.verbose == True or g.debug == True:
            print("LINE: ", line)

        match = re.search(pattern, line)
        if match != None:
            output = match.groups()
            if g.verbose == True or g.debug == True:
                print('MATCHED pattern')
            break

    return output
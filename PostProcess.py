import sys, time
import Commands
import Checker as check
from multiprocessing import Process
import multiprocessing
import Async
import math


### Translate LBA to Bucket
def lba_to_bucket(g, lba):
    bucket = (int(lba) * int(g.sector_size)) / int(g.bucket_size)
    if bucket > g.num_buckets:
        bucket = g.num_buckets - 1
    return bucket


### Translate Bucket to LBA
def bucket_to_lba(g, bucket):
    lba = (bucket * g.bucket_size) / g.sector_size
    return lba


### Get logrithmic theta for Zipfian distribution
def theta_log(g, base, value):
    check.debug_print(g, "base=" + str(base) + ", value=" + str(value))
    if value == 0 or base == 0:
        return 0
    else:
        result = math.log(value) / math.log(base)
        return result
    

### Print Results
def print_results(g):
    buffer=''
    row=0
    column=0
    bw_total=0
    counts={}
    read_sum=0
    write_sum=0
    row=column=0
    bw_total=0
    histogram_iops=[]
    histogram_bw=[]
    

    check.verbose_print(g, "num_buckets=" + str(g.num_buckets) + " bucket_size=" + str(g.bucket_size))
    x=0
    threshold = g.num_buckets / 100
    i=0

    while i < int(g.num_buckets):
        x += 1
        if x > threshold:
            check.printf("\rBucket Percent: %d %% (%d of %d)", ((i * 100)/ g.num_buckets), i, g.num_buckets)
            sys.stdout.flush()
            x=0
        if i != 0 and (i % g.x_width) == 0:
            buffer=''
            row += 1
            column=0
        
        r=0
        if i in g.reads:
            r=g.reads[i]
        w=0
        if i in g.writes:
            w=g.writes[i]

        bucket_total = r + w
        bw_total += bucket_total * g.bucket_size
        if bucket_total in counts:
            counts[bucket_total] += 1
        else:
            counts[bucket_total] = 1

        check.debug_print(g, " bucket_total=" + str(bucket_total) + " counts[b_bucket_total]=" + str(counts[bucket_total]))
        read_sum += r
        write_sum += w
        buffer = buffer + ("%d " % bucket_total)
        column += 1
        i += 1

    print("\r")
    while (i % g.x_width) != 0:
        i+=1
        buffer = buffer + "0 "

    check.verbose_print(g, "num_buckets=%s pfgp iot=%s bht=%s r_sum=%s w_sum=%s yheight=%s, counts=%d" % (g.num_buckets, g.io_total.value, g.bucket_hits_total.value, read_sum, write_sum, g.y_height, len(counts)))

    t=0
    section_count=0
    b_count=0
    gb_tot = 0
    bw_tot = 0
    bw_count = 0
    io_sum = 0
    tot = 0

    max_set = 0
    max = 0
    theta_count = 1
    theta_total = 0
    max_theta = 0
    min_theta = 999


    # %counts is a hash
    # each key "bucket_total" represents a particular I/O count for a bucket
    # each value represents the number of buckets that had this I/O count
    # This allows us to quickly tally up a histogram and is pretty
    # space efficient since most buckets tend to have zero I/O that
    # key tends to have the largest number of buckets
    #
    # Iterate through each key in decending order
    for total in sorted(counts, reverse=True):
        check.debug_print(g, "total=" + str(total) + " counts=" + str(counts[total]))
        if total > 0:
            tot += total * counts[total]
            if max_set == 0:
                max_set=1
                max = total
            else:
                theta_count += 1
                min = total
                cur_theta = theta_log(g, theta_count, max) - theta_log(g, theta_count, total)
                if cur_theta > max_theta:
                    max_theta = cur_theta
                if cur_theta < min_theta:
                    min_theta = cur_theta
                check.debug_print(g, "cur_theta=" + str(cur_theta))
                theta_total += cur_theta
            i=0
            while i<counts[total]:
                section_count += total
                b_count += 1
                bw_count += total * g.bucket_size
                if ((b_count * g.bucket_size )/ g.GiB) > (g.percent * g.total_capacity_gib):
                    check.debug_print(g, "b_count:" + str(b_count))
                    bw_tot += bw_count
                    gb_tot += (b_count * g.bucket_size)
                    io_sum += section_count
    
                    gb = "%.1f" % (gb_tot / g.GiB)
                    if g.bucket_hits_total.value == 0:
                        io_perc = "NA"
                        io_sum_perc = "NA"
                        bw_perc = "NA"
                    else:
                        check.debug_print(g, "b_count=" + str(b_count) + " s=" + str(section_count) + " ios=" + str(io_sum) + " bwc=" + str(bw_count))
                        io_perc = "%.1f" % ((float(section_count) / float(g.bucket_hits_total.value)) * 100.0)
                        io_sum_perc = "%.1f" % ((float(io_sum) / float(g.bucket_hits_total.value)) * 100.0)
                        if bw_total == 0:
                            bw_perc = "%.1f" % (0)
                        else:
                            bw_perc = "%.1f" % ((bw_count / bw_total) * 100)
                    
                    histogram_iops.append(str(gb) + " GB " + str(io_perc) + "% (" + io_sum_perc + "% cumulative)")
                    histogram_bw.append(str(gb) + " GB " + str(bw_perc) + "% ")

                    b_count=0
                    section_count=0
                    bw_count=0
                    
                i += 1
    if b_count:
        check.debug_print(g, "b_count: " + str(b_count))
        bw_tot += bw_count
        gb_tot += b_count * g.bucket_size
        io_sum += section_count

        gb = "%.1f" % (gb_tot / g.GiB)
        if g.bucket_hits_total.value == 0:
            io_perc = "NA"
            io_sum_perc = "NA"
            bw_perc = "NA"
        else:
            io_perc = "%.1f" % ((section_count / g.bucket_hits_total.value) * 100)
            io_sum_perc = "%.1f" % ((io_sum / g.bucket_hits_total.value) * 100)
            if bw_total == 0:
                bw_perc = "%.1f" % (0)
            else:
                bw_perc = "%.1f" % ((bw_count / bw_total) * 100)


        histogram_iops.append(str(gb) + " GB " + str(io_perc) + "% (" + str(io_sum_perc) + "% cumulative)")
        histogram_bw.append(str(gb) + " GB " + str(bw_perc) + "% ")

        b_count = 0
        section_count = 0
        bw_count = 0

    check.debug_print(g, "t=" + str(t))

    print("--------------------------------------------")
    print("Histogram IOPS:")
    for entry in histogram_iops:
        print(entry)
    print("--------------------------------------------")
    print("--------------------------------------------")
    

    if (theta_count):
        avg_theta = theta_total / theta_count
        med_theta = ((max_theta - min_theta) / 2 ) + min_theta
        approx_theta = (avg_theta + med_theta) / 2
        #string = "avg_t=%s med_t=%s approx_t=%s min_t=%s max_t=%s\n" % (avg_theta, med_theta, approx_theta, min_theta, max_theta)
        check.verbose_print(g, "avg_t=%s med_t=%s approx_t=%s min_t=%s max_t=%s\n" % (avg_theta, med_theta, approx_theta, min_theta, max_theta))
        analysis_histogram_iops = "Approximate Zipfian Theta Range: %0.4f-%0.4f (est. %0.4f).\n" % (min_theta, max_theta, approx_theta)
        print(analysis_histogram_iops)
    
    return


def post_process(g):
    g.THREAD_MAX = multiprocessing.cpu_count() * 4

    cmd = 'tar -tf ' + g.tarfile 
    print(g.tarfile)

    file_text = Commands.run_cmd(g, cmd)
    check.debug_print(g, file_text)

    file_list = []
    for i in file_text.split("\n"):
        check.debug_print(g, "i=" + i)
        if i != "":
            file_list.append(i)
        
    print("Unpacking " + g.tarfile + ".  This may take a minute")
    cmd = 'tar -xvf ' + g.tarfile
    out = Commands.run_cmd(g, cmd)

    out = Commands.run_cmd(g, 'cat '+ g.fdisk_file )
    result = check.regex_find(g, "Units = sectors of \d+ \S \d+ = (\d+) bytes", out)
    if result == False:
        #Units: sectors of 1 * 512 = 512 bytes
        result = check.regex_find(g, "Units: sectors of \d+ \* \d+ = (\d+) bytes", out)
        if result == False:
            print("ERROR: Sector Size Invalid")
            sys.exit()
    g.sector_size = int(result[0])
    check.verbose_print(g, "sector size=" + str(g.sector_size))
    result = check.regex_find(g, ".+ total (\d+) sectors", out)
    if result == False:
        #Disk /dev/sdb: 111.8 GiB, 120034123776 bytes, 234441648 sectors
        result = check.regex_find(g, "Disk \/dev\/\w+-\d+: \d+.* GiB, \d+ bytes, (\d+) sectors", out)
        if result == False:
            print("ERROR: Total LBAs is Invalid")
            sys.exit()
    g.total_lbas  = int(result[0])
    check.verbose_print(g, "sector count ="+ str(g.total_lbas))

    result = check.regex_find(g, "Disk (\S+): \S+ GB, \d+ bytes", out)
    if result == False:
        # LINE:  Disk /dev/sdb: 111.8 GiB, 120034123776 bytes, 234441648 sectors
        result = check.regex_find(g, "Disk (\S+):", out)
        if result == False:
            print("ERROR: Device Name is Invalid")
            sys.exit()
    g.device = result[0]
    check.verbose_print(g, "dev="+ g.device + " lbas=" + str(g.total_lbas) + " sec_size=" + str(g.sector_size))

    g.total_capacity_gib = g.total_lbas * g.sector_size / g.GiB
    check.printf("lbas: %d sec_size: %d total: %0.2f GiB\n", g.total_lbas, g.sector_size, g.total_capacity_gib)

    g.num_buckets = g.total_lbas * g.sector_size / g.bucket_size

    g.y_height = g.x_width = int(math.sqrt(g.num_buckets))
    check.debug_print(g, "x=" + str(g.x_width) + " y=" + str(g.y_height))

    check.debug_print(g, "num_buckets=" + str(g.num_buckets) + " sector_size=" + str(g.sector_size) + " total_lbas=" + str(g.total_lbas) + " bucket_size=" + str(g.bucket_size))
    Commands.run_sys_cmd("rm -f filetrace." + g.device_str + ".*.txt")
    Commands.run_sys_cmd("rm -f blk.out." + g.device_str + ".*.blkparse")

    print("Time to parse.  Please wait...\n")
    size = len(file_list)
    file_count = 0

    plist = []
    for filename in file_list:
        file_count += 1
        check.printf("\rInput Percent: %d %% (File %d of %d) threads=%d", (file_count*100 / size), file_count, size, len(plist))
        sys.stdout.flush()

        result = check.regex_find(g, "(blk.out.\S+).gz", filename)
        if result != False:
            new_file = result[0]
            p = Process(target=Async.thread_parse, args=(g, new_file, file_count))
            plist.append(p)
            p.start()

        while len(plist) > g.thread_max:
            for p in plist:
                try:
                    p.join(0)
                except:
                    pass
                else:
                    if not p.is_alive():
                        plist.remove(p)
            time.sleep(0.10)

    x=1
    while len(plist) > 0:
        dots=""
        for i in range(x):
            dots = dots + "."
        x+=1
        if x>3:
            x=1
        check.printf("\rWaiting on %3d threads to complete processing%-3s", len(plist), dots)
        check.printf("    ")
        sys.stdout.flush()
        for p in plist:
            try:
                p.join(0)
            except:
                pass
            else:
                if not p.is_alive():
                    plist.remove(p)
        time.sleep(0.10)

    print("\rFinished parsing files.  Now to analyze         \n")
    print_results(g)
    Commands.cleanup_files(g)
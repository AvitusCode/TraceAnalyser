import os, sys
import Checker as check
import Parser as parse


### Combine thread-local counts into global counts
def total_thread_counts(g, num):
    g.total_semaphore.acquire()
    check.debug_print(g, "Thread " + str(num) + " has total lock t=" + str(g.thread_io_total) + " g=" + str(g.io_total.value))
    g.io_total.value += g.thread_io_total
    check.debug_print(g, "Thread " + str(num) + " releasing total lock t=" + str(g.thread_io_total) + " g=" + str(g.io_total.value))
    g.total_semaphore.release()

    g.read_semaphore.acquire()
    check.debug_print(g, "Thread " + str(num) + " has read lock.")
    for bucket, value in g.thread_reads.items():
        try:
            g.reads[bucket] += value
        except:
            g.reads[bucket] = value
        check.debug_print(g, "Thread " + str(num) + " has read lock.  Bucket=" + str(bucket) + " Value=" + str(value) + " g.reads[bucket]=" + str(g.reads[bucket]))
    g.read_semaphore.release()

    g.write_semaphore.acquire()
    check.debug_print(g, "Thread " + str(num) + " has write lock.")
    for bucket, value in g.thread_writes.items():
        try:
            g.writes[bucket] += value
        except:
            g.writes[bucket] = value
        check.debug_print(g, "Thread " + str(num) + " has write lock.  Bucket=" + str(bucket) + " Value=" + str(value) + " g.writes[bucket]=" + str(g.writes[bucket]))
    g.write_semaphore.release()

    g.total_semaphore.acquire()
    check.debug_print(g, "Thread " + str(num) + " has total lock t=" + str(g.thread_bucket_hits_total) + " g=" + str(g.bucket_hits_total.value))
    g.bucket_hits_total.value += g.thread_bucket_hits_total
    check.debug_print(g, "Thread " + str(num) + " releasing total lock t=" + str(g.thread_bucket_hits_total) + " g=" + str(g.bucket_hits_total.value))
    g.total_semaphore.release()

    return


### Thread parse routine for blktrace output
def thread_parse(g, file, num):
    os.system("gunzip " + file + ".gz")
    check.debug_print(g, "\nSTART: " +  file + " " + str(num) + "\n")
    try:
        fo = open(file, "r")
    except:
        print("ERROR: Failed to open " + file)
        sys.exit(3)
    else:
        count=0
        hit_count = 0
        for line in fo:
            count += 1
            result_set = check.regex_find(g, '(\S+)\s+Q\s+(\S+)\s+(\S+)$', line)
            if result_set:
                hit_count += 1
                try:
                    parse.parse_trace(g, result_set[0], int(result_set[1]), int(result_set[2]))
                except:
                    print("PARSE EXCEPT")
                    pass
            #sys.stdout.flush()
        fo.close()
        total_thread_counts(g, num)
        check.debug_print(g,  "\n FINISH" + file +  " (" + str(count) + " lines) [hit_count=" + str(hit_count) + "]" + str(g.thread_io_total) + "\n")
        rc = os.system("rm -f " + file)

    return
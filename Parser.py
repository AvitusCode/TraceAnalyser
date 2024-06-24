import Checker as check

from collections import Counter
from functools import reduce
from Filters import FiltersFactory
from Filters import FilterType
from BlkEntry import BlkEntry, SeqDetector
from PredictedEntry import PredictedEntry
import Plotter
from Utility import Item, PairSet 
from BlkWatcher import watch_block_pattern_per_time


def to_page_range(entry):
    """
    Contructs a range object from a single entry for the pages it accessed.

    Range has increments of 8 because page access in the traces are in multiples of 8.
    """
    sector, blocks = entry.get_lba_blocks()
    return range(sector, sector + blocks, 8)


def count_page_access(counter, arange):
    for i in arange:
        counter[i] += 1
    return counter


def load_filtered_data_simple(g, file, filters_factory):
    filter_fn = filters_factory.get_filter(FilterType.SIMPLE)
    try:
        blk_entries = BlkEntry.generate_from_file(g, file)
        blk_entries = filter(filter_fn, blk_entries)
        return blk_entries
    except Exception as ex:
        print("ERROR: parse blk data" + repr(ex))

    return None


def load_filtered_data_predicted(g, file, filters_factory):
    filter_fn = filters_factory.get_filter(FilterType.PREDICTED)
    try:
        p_entries = PredictedEntry.generate_from_file(g, file)
        p_entries = filter(filter_fn, p_entries)
        return p_entries
    except Exception as ex:
        print("ERROR: parse blk data" + repr(ex))

    return None


def pase_freq_hist(g, blk_data):
    io_size = []
    weight = g.block_size / 1024
    
    for item in blk_data:        
        _, blocks = item.get_lba_blocks()
        io_size.append(int(weight * blocks))
    
    Plotter.freq_hist(g, io_size, title="IO size")


def parse_block_io_size_per_time(g, blk_data):
    io_size = []
    io_time = []
    weight = g.block_size / 1024
    
    for item in blk_data:        
        _, blocks = item.get_lba_blocks()
        io_size.append(int(weight * blocks))
        io_time.append(item.time)

    Plotter.block_time_io_plot(io_time, io_size, g.parseaction)
    

def load_predicted(g):
    predicted = PairSet()
    with open(g.pp_file, "r") as file:
            p_data = load_filtered_data_predicted(g, file, FiltersFactory(g))
            for [_, p_sector, p_size] in p_data:
                predicted.insert(Item(p_sector, p_size / g.weight))
    return predicted


def process_detect(g, blk_prev, blk_cur, detector: SeqDetector):
    detector.set_blk(blk_prev)
    if detector.detect(blk_cur):
        if g.cut_seq:
            return True # Continue 
    else:
        detector.collect()
    
    return False # Nor Continue


class SingletonIterator(object):
    """Proxy iterator to allow 'iteration' over a fictitious sequence
    holding a single element, the `value`."""
    def __init__(self, value):
        self._value = value
        self._yielded = False

    def __iter__(self):
        return self

    def __next__(self):
        if self._yielded:
            raise StopIteration
        self._yielded = True
        return self._value
    

def parse_time_lba(g, blk_data):   
    counter = 0
    lba_data = []
    lba_data.append(Plotter.ConfigLbaOp([], [], [], "blue", "green", "R({})".format(g.selected_thread)))
    lba_data.append(Plotter.ConfigLbaOp([], [], [], "red", "green", "W({})".format(g.selected_thread)))
    blk_iter = iter(blk_data)
    
    try: 
        blk_cur = next(blk_iter)
    except StopIteration:
        print("Error: empty generator")
        return
    
    seq_read = SeqDetector("R")
    seq_write = SeqDetector("W")

    predicted = PairSet()
    if g.with_predicted:
        predicted = load_predicted(g)

    while True:
        try:        
            blk_prev = blk_cur
            blk_cur = next(blk_iter)

            counter += 1

            if process_detect(g, blk_prev, blk_cur, seq_read):
                continue
            if process_detect(g, blk_prev, blk_cur, seq_write):
                continue

            lba, size = blk_prev.get_lba_blocks()
            time = blk_prev.time
            op = blk_prev.rwbs
            time_step = (blk_cur.time - blk_prev.time) / (size / 8)

            is_predicted: bool = g.with_predicted and (Item(lba, size) in predicted)
            
            size += 1
            for step in range(0, size, 8):
                is_write = int(op in ("W", "WS"))
                lba_data[is_write].lba_axis_data.append(Plotter.LbaPack(lba + step, is_predicted))
                lba_data[is_write].time_axis.append(time)
                time += time_step
        except StopIteration:
            break

    seq_read.collect()
    seq_write.collect()

    if counter > 1:
        lba_data[1].sequanced = seq_write.get_sequence_list()
        lba_data[0].sequanced = seq_read.get_sequence_list()
        Plotter.lba_time(g, lba_data)


def to_parse_blk_info(g):
    with open(g.parsefile, "r") as file:
        blk_data = load_filtered_data_simple(g, file, FiltersFactory(g))
        if not blk_data:
            return

        match g.parsemode:
            case "hf":
                pase_freq_hist(g, blk_data)
            case "tlba":
                parse_time_lba(g, blk_data)
            case "blkp":
                watch_block_pattern_per_time(g, blk_data)
            case "iobt":
                parse_block_io_size_per_time(g, blk_data)
            case _:
                ranges = map(to_page_range, blk_data)
                counter = reduce(count_page_access, ranges, Counter())
                print('DBG: Excuse me, but you just entered the dead zone')


### Parse blktrace output
def parse_trace(g, rw, lba, size):
    check.debug_print(g, "rw=" + rw + " lba=" + str(lba) + " size=" + str(size))
    if (rw == "R") or (rw == "RW") or (rw == "RS"):
        # Read
        g.thread_io_total += 1

        bucket_hits = (size * g.sector_size) / g.bucket_size
        if ((size * g.sector_size) % g.bucket_size) != 0:
            bucket_hits += 1

        bucket_hits = int(bucket_hits)
        for i in range(0, bucket_hits):
            bucket = int((lba * g.sector_size) / g.bucket_size) + i
            if bucket > g.num_buckets:
                bucket = g.num_buckets - 1

            if bucket in g.thread_reads:
                g.thread_reads[bucket] += 1
            else:
                g.thread_reads[bucket] = 1

    elif (rw == "W") or (rw == "WS"):
        # Write
        g.thread_io_total += 1

        bucket_hits = (size * g.sector_size) / g.bucket_size
        if ((size * g.sector_size) % g.bucket_size) != 0:
            bucket_hits += 1

        bucket_hits = int(bucket_hits)
        for i in range(0, bucket_hits):
            bucket = int((lba * g.sector_size) / g.bucket_size) + i
            if bucket > g.num_buckets:
                bucket = g.num_buckets - 1

            if bucket in g.thread_writes:
                g.thread_writes[bucket] += 1
            else:
                g.thread_writes[bucket] = 1
    return

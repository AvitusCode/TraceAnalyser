from collections import Counter
from Plotter import freq_hist
import numpy as np


def cosine_similarity(x, y):
    norm_x = np.sqrt(sum(x))
    norm_y = np.sqrt(sum(y))

    return np.dot(x, y) / (norm_x * norm_y)


def collect_feature_vec(blk_data_list):
    feature_vec = [0 for _ in range(128)]
    counted_blocks = Counter(blk_data_list)
    denom = 0.0

    for block, count in counted_blocks.items():
        feature_vec[int(block / 4) - 1] = count
        denom += count * count

    denom = np.sqrt(denom)
    # normalize feature vec
    feature_vec = [float(x) / denom for x in feature_vec]
    
    return feature_vec


def pattern_reporter(blk_pattern_history):
    cos_sim = cosine_similarity(blk_pattern_history[0], blk_pattern_history[1])
    blk_pattern_history[0] = blk_pattern_history[1]
    blk_pattern_history.pop()
    return cos_sim


def watch_block_pattern_per_time(g, blk_data):
    weight = g.block_size / 1024
    blk_data_list = []
    start_time = g.time_period_start
    blk_pattern_history = []
    history_count = 0
    idx = 0
    
    for item in blk_data:
        if item.time <= start_time + g.time_cover:
            _, block_size = item.get_lba_blocks()
            blk_data_list.append(int(block_size * weight))
        else:
            if len(blk_data_list) == 0:
                start_time += g.time_cover
                idx += 1
                continue
            freq_hist(g, blk_data_list, title="time period [{}, {}]".format(start_time, start_time + g.time_cover), show=False, idx=idx)
            blk_pattern_history.append(collect_feature_vec(blk_data_list))
            
            start_time += g.time_cover
            history_count += 1
            idx += 1
            blk_data_list = []
        
        if history_count == 2:
            cos_sim = pattern_reporter(blk_pattern_history)
            print("diap: {}, similarity: {}".format(idx, cos_sim))
            history_count -= 1

    if len(blk_pattern_history) == 1 and len(blk_data_list) > 0:
        freq_hist(g, blk_data_list, title="time period [{}, {}]".format(start_time, start_time + g.time_cover), show=False, idx=idx)
        blk_pattern_history.append(collect_feature_vec(blk_data_list))
        cos_sim = pattern_reporter(blk_pattern_history)
        print("diap: {}, similarity: {}".format(idx, cos_sim))

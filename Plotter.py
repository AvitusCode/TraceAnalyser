import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import (PercentFormatter, FuncFormatter)


def time_formatter(x, pos):
    return "{:.2f}sec".format(x)

def sector_formatter(x, pos):
    return "{:.0f}".format(x)

def frequancy_formatter(x, pos):
    return "{}K".format(x)


class ConfigLbaOp(object):
    def __init__(self, lba_axis_data, time_axis, secuanced, color, title) -> None:
        self.lba_axis_data = lba_axis_data
        self.time_axis = time_axis
        self.sequanced = secuanced
        self.color = color
        self.title = title


def freq_hist(g, data, title, show=True, idx=0):
    fig = plt.figure(figsize=(10, 10), dpi=100)
    ax = fig.add_subplot(111)
    max_elem = max(data)
    ax.hist(data, edgecolor="red", bins=max_elem, weights=np.ones_like(data) * 100 / len(data))
    ax.yaxis.set_major_formatter(PercentFormatter())
    ax.xaxis.set_major_formatter(FuncFormatter(frequancy_formatter))
    ax.set_xticks(np.arange(0, max_elem + 1, 4))
    ax.grid()
    ax.set_title(title)
    ax.set_ylabel("Frequancy")
    ax.set_xlabel("IO size in blocks")
    
    if show:
        plt.show()
    else:
        fig.savefig('res/block_pattern_predict/' + g.parsefile + '_' + str(idx) +'_hf.png', dpi=100)


def block_time_io_plot(io_time = None, io_block = None, title=''):
    if io_block == None or io_time == None:
        return
    fig = plt.figure(figsize=(10, 10), dpi=100)
    ax = fig.add_subplot(111)
    ax.set_yticks(np.arange(0, max(io_block) + 1, 4))
    ax.scatter(io_time, io_block, color='red', label=title, s=2)
    ax.grid()
    ax.set_title('Io size per time')
    ax.set_xlabel('time')
    ax.set_ylabel('block size')
    plt.show()


def prepare_some_plot(g, item, ax, title, x_label, y_label):
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.yaxis.set_major_formatter(FuncFormatter(time_formatter))
    ax.xaxis.set_major_formatter(FuncFormatter(sector_formatter))
    ax.grid()

    weight = g.sector_size / g.weight
    lba_print_data = [weight * lba for lba in item.lba_axis_data]

    ax.scatter(lba_print_data, item.time_axis, color=item.color, label=item.title, s=2)


def prepare_seq_plot(g, item, ax, title, x_label, y_label):
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.yaxis.set_major_formatter(FuncFormatter(time_formatter))
    ax.xaxis.set_major_formatter(FuncFormatter(sector_formatter))
    ax.grid()

    weight = g.sector_size / g.weight
    for s in item.sequanced:
        print_data = [weight * lba for lba in s[0]]
        ax.plot(print_data, s[1], color=item.color)


def lba_time(g, config_lba_data):
    fig = plt.figure(figsize=(10, 10), dpi=100)

    if g.plot_mode == "A":
        ax1 = fig.add_subplot(221)
        prepare_some_plot(g, config_lba_data[1], ax1, "Writes", g.plot_format, "time")

        ax2 = fig.add_subplot(223)
        prepare_some_plot(g, config_lba_data[0], ax2, "Reads", g.plot_format, "time")

        ax3 = fig.add_subplot(222)
        prepare_seq_plot(g, config_lba_data[1], ax3, "Write seq", g.plot_format, "time")

        ax4 = fig.add_subplot(224)
        prepare_seq_plot(g, config_lba_data[0], ax4, "Read seq", g.plot_format, "time")
    elif g.plot_mode == "W":
        axw = fig.add_subplot(121)
        prepare_some_plot(g, config_lba_data[1], axw, "Writes", g.plot_format, "time")
        axsw = fig.add_subplot(122)
        prepare_seq_plot(g, config_lba_data[1], axsw, "Write seq", g.plot_format, "time")
    elif g.plot_mode == "R":
        axr = fig.add_subplot(121)
        prepare_some_plot(g, config_lba_data[0], axr, "Reads", g.plot_format, "time")
        axsr = fig.add_subplot(122)
        prepare_seq_plot(g, config_lba_data[0], axsr, "Read seq", g.plot_format, "time")
    elif g.plot_mode == "WO":
        ax = fig.add_subplot(111)
        prepare_some_plot(g, config_lba_data[1], ax, "Writes", g.plot_format, "time")
    elif g.plot_mode == "RO":
        ax = fig.add_subplot(111)
        prepare_some_plot(g, config_lba_data[0], ax, "Reads", g.plot_format, "time")
    else:
        print("Plot mode error, actual option is " + g.plot_mode)

    plt.show()
    # fig.savefig('res/' + g.parsefile + '_lba_time.png', dpi=100)

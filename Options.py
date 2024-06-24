from multiprocessing import Manager, Value

class pIONOptions(object):
    def __init__(self):
        self.version           = "0.1.0"                     # Version string
        self.verbose           = False                       # Verbose logging (-v flag)
        self.debug             = False                       # Debug log level (-x flag)
        self.manager           = Manager()                   # Multiprocess sync object

        self.io_total          = Value('L', 0)               # Number of total I/O's
        self.reads             = self.manager.dict()         # Array of read hits by bucket ID
        self.writes            = self.manager.dict()         # Array of write hits by bucket ID
        self.bucket_hits_total = Value('L', 0)               # Total number of bucket hits (not the total buckets)
        self.total_blocks      = Value('L', 0)               # Total number of LBA's accessed during profiling

        ### Semaphores: These are the locks for the shared variables
        self.read_semaphore            = self.manager.Lock() # Lock for the global read hit array
        self.write_semaphore           = self.manager.Lock() # Lock for the global write hit array
        self.total_semaphore           = self.manager.Lock() # Lock for the global I/O totals

        # Thread-local variables.  Use these to avoid locking constantly
        self.thread_io_total   = 0          # Thread-local total I/O count (I/O ops)
        self.thread_bucket_hits_total = 0   # Thread-local total bucket hits (buckets)
        self.thread_reads = {}              # Thread-local read count hash (buckets)
        self.thread_writes = {}             # Thread-local write count hash (buckets)

        # Globale
        self.cleanup           = []         # Files to delete after running this script
        self.total_lbas        = 0          # Total logical blocks, regardless of sector size
        self.tarfile           = ''         # .tar file outputted from 'trace' mode
        self.fdisk_file        = ""         # File capture of fdisk tool output

        self.device            = ''         # Device (e.g. /dev/sdb)
        self.device_str        = ''         # Device string (e.g. sdb for /dev/sdb)

        # Unit Scales
        self.KiB               = 1024       # 2^10
        self.MiB               = 1048576    # 2^20
        self.GiB               = 1073741824 # 2^30

        # Parse settings for blkparse output
        self.input_dir         = 'traces/'  # source dir with traces
        self.output_file       = ''         # output data for something you need
        self.parsefile         = ''         # file with blkparse standart output
        self.parseaction       = ''         # action for parsing
        self.parsemode         = ''         # parse operations

        # Config settings
        self.bucket_size        = 1 * self.MiB # Size of the bucket for totaling I/O counts (e.g. 1MB buckets)
        self.num_buckets        = 1            # Number of total buckets for this device
        self.timeout            = 3            # Seconds between each print
        self.runtime            = 0            # Runtime for 'live' and 'trace' modes
        self.live_itterations   = 0            # How many iterations for live mode.  Each iteration is 'timeout' seconds long
        self.sector_size        = 512          # Sector size (usually obtained with fdisk)
        self.block_size         = 512
        self.percent            = 0.020        # Histogram threshold for each level (e.g. 0.02% of total drive size)
        self.total_capacity_gib = 0            # Total drive capacity
        self.mode               = ''           # Processing mode (live, trace, post)
        self.thread_max         = 8            # Max thread cout
        self.buffer_size        = 1024         # blktrace buffer size
        self.buffer_count       = 8            # blktrace buffer count
        self.thread_mode        = False        # Parse data only for a specific thread
        self.cpu_mode           = False        # Parse data only for a specific cpu
        self.selected_thread    = 0            # A selected thread
        self.selected_cpu       = 0            # A selected cpu

        # plot settings
        self.x_width            = 1280          # plot x-width
        self.y_height           = 1280          # plot y-height
        self.weight             = 10**9         # one GB
        self.plot_mode          = 'A'           # Plot mode (A, W, R, WO, RO)
        self.plot_format        = ''            # x axis label
        self.time_period_start  = 0.0           # start time for data analys
        self.time_period_end    = 10**9         # end time for data analys
        self.sector_start       = 0
        self.sector_end         = 0
        self.cut_seq            = True          # cut sequential io from all trace
        self.time_cover         = 1             # select timeperiod in seconds for block pattern analysis per time.

        # For predicted result
        self.with_predicted     = False
        self.pp_file            = "_"
        
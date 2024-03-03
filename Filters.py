LEGAL_ACTIONS = {
    "A",  # IO was remapped to a different device
    "B",  # IO bounced
    "C",  # IO completion
    "D",  # IO issued to driver
    "F",  # IO front merged with request on queue
    "G",  # Get request
    "I",  # IO inserted onto request queue
    "M",  # IO back merged with request on queue
    "P",  # Plug request
    "Q",  # IO handled by request queue code
    "S",  # Sleep request
    "T",  # Unplug due to timeout
    "U",  # Unplug request
    "X",  # Split
}

LEGAL_RWBS = {
    "D",  # discard
    "W",  # write
    "R",  # read
    "N",  # None of the above
    "F",  # FUA
    "A",  # readahead
    "S",  # sync
    "M",  # metadata
    "RS", # read sync
}

def action_filter(action):
    if action not in LEGAL_ACTIONS:
        raise ValueError("{} is not an valid action".format(action))

    def filter_fn(entry):
        return entry.action == action

    return filter_fn


def rwbs_filter(rwbs):
    if rwbs not in LEGAL_RWBS:
        raise ValueError("{} is not an valid rwbs".format(rwbs))

    def filter_fn(entry):
        return rwbs in entry.rwbs

    return filter_fn


# A predicate that returns True if the entry is a complete action
complete = action_filter("C")

# A predicate that returns True if the entry is a write rwbs
write = rwbs_filter("W")

# A predicate that returns True if the entry is a read rwbs
read      = rwbs_filter("R")
read_sync = rwbs_filter("RS")

# making aggregated action, that relied on global options

def write_filter_fn(entry):
    """
    A predicate that returns True for complete actions that are writes.
    """
    return complete(entry) and write(entry)


def read_filter_fn(entry):
    """
    A predicate that returns True for complete actions that are reads.
    """
    return complete(entry) and read(entry)


def read_sync_filter_fn(entry):
    """
    A predicate that returns True for complete actions that are reads.
    """
    return complete(entry) and read_sync(entry)


def all_filter_fn(entry):
    """
    A predicate that returns True for complete actions that are writes or reads.
    """
    return write_filter_fn(entry) or read_filter_fn(entry) or read_sync_filter_fn(entry)


class FiltersFactory(object):
    def __init__(self, g) -> None:
        self.g = g

    def get_filter(self):

        def filter_fn(entry):
            is_pass: bool = True
            
            match self.g.parseaction:
                case 'A':
                    is_pass = is_pass and write_filter_fn(entry) or read_filter_fn(entry)
                case 'W':
                    is_pass = is_pass and write_filter_fn(entry)
                case 'R':
                    is_pass = is_pass and read_filter_fn(entry)
                case 'RS':
                    is_pass = is_pass and read_sync_filter_fn(entry)
                case _:
                    is_pass = False
            
            if self.g.thread_mode:
                is_pass = is_pass and entry.pid == self.g.selected_thread

            is_pass = is_pass and (self.g.time_period_start <= entry.time <= self.g.time_period_end)
            is_pass = is_pass and (self.g.sector_start <= entry.sector <= self.g.sector_end)

            return is_pass
        
        return filter_fn

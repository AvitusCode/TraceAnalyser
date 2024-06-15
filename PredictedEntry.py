from Checker import debug_print


class PredictedEntry(object):
    '''
    Read and collect a predicted data
    '''
    FORMATTER = '[{pid}]: {sector}, {size}'

    def __init__(self, pid, sector, size):
        self.pid = pid
        self.sector = sector
        self.size = size

    def __repr__(self):
        return PredictedEntry.FORMATTER.format(**self.__dict__)
    
    def __iter__(self):
        return iter(
            [
                self.pid,
                self.sector,
                self.size
            ]
        )

    @staticmethod
    def parse_tokens(line_source):
        data = line_source.split()
        pid = int(data[0])
        sector = int(data[1])
        size = int(data[2])
        return PredictedEntry(pid, sector, size)

    
    @staticmethod
    def generate_from_file(g, file):
        with file:
            for line in file:
                try:
                    yield PredictedEntry.parse_tokens(line)
                except (ValueError, Exception):
                    debug_print(g, 'Parse Error (Unexpected Format):\n\t{}'.format(line))

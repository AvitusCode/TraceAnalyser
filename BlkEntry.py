from Checker import debug_print
import re

class BlkEntry(object):
    FORMATTER = '{major:3d},{minor:<3d} {cpu:2d} {seq:8d} {time:14.9f} {pid:5d} {action:>2} {rwbs:>3} {sector} {size}'

    def __init__(self, major, minor, cpu, seq, time, pid, action, rwbs, sector, size):
        self.major = major
        self.minor = minor
        self.cpu = cpu
        self.seq = seq
        self.time = time
        self.pid = pid
        self.action = action.strip()
        self.rwbs = rwbs.strip()
        self.sector = sector
        self.size = size

    def __repr__(self):
        """
        prints the entry in the the same representation as the default blkparse output.
        """
        return BlkEntry.FORMATTER.format(**self.__dict__)
    
    def __iter__(self):
        return iter(
            [
                self.major,
                self.minor,
                self.cpu,
                self.seq,
                self.time,
                self.pid,
                self.action,
                self.rwbs,
                self.sector,
                self.size,
            ]
        )
    
    def get_lba_blocks(self):
        return self.sector, self.size

    @staticmethod
    def parse(line_source):
        line = line_source.split()
        if len(line) < 8:
            raise ValueError
        
        major, minor = line[0].split(',')
        major = int(major)
        minor = int(minor)
        cpu = int(line[1])
        seq = int(line[2])
        time = float(line[3])
        pid = int(line[4])
        action = line[5]
        rwbs = line[6]
        sector = int(line[7])
        size = int(line[9])
        return BlkEntry(major, minor, cpu, seq, time, pid, action, rwbs, sector, size)
    
    @staticmethod
    def parse_tokens(line_source):
        tokens = re.split(",|[\s]+", line_source)
        major = int(tokens[0])
        minor = int(tokens[1])
        cpu = int(tokens[2])
        seq = int(tokens[3])
        time = float(tokens[4])
        pid = int(tokens[5])
        action = tokens[6]
        rwbs = tokens[7]
        try:
            sector = int(tokens[8])
            size = int(tokens[10])
        except ValueError:
            sector = 0
            size = 0
        except IndexError:
            sector = 0
            size = 0

        return (
            BlkEntry(major, minor, cpu, seq, time, pid, action, rwbs, sector, size),
            tokens,
        )
    
    @staticmethod
    def generate_from_file(g, f):
        with f:
            for line in f:
                try:
                    yield BlkEntry.parse(line)
                except (ValueError, Exception):
                    debug_print(g, 'Parse Error (Unexpected Format):\n\t{}'.format(line))


class SeqDetector(object):
    def __init__(self, op) -> None:
        self._op = op
        self._cur_blk_entry: BlkEntry
        self._sequence_list = []
        self._sequence = []
        self._time = []

    def set_blk(self, blk_entry: BlkEntry):
        self._cur_blk_entry = blk_entry

    def detect(self, next_blk_entry: BlkEntry):
        if next_blk_entry.rwbs != self._op:
            return False
        
        result: bool = self._cur_blk_entry.sector + self._cur_blk_entry.size == next_blk_entry.sector

        if result:
            self._sequence.append(self._cur_blk_entry.sector)
            self._time.append(self._cur_blk_entry.time)
            self._cur_blk_entry = next_blk_entry

        return result
    
    def collect(self):
        if len(self._sequence) > 1:
            self._sequence.append(self._cur_blk_entry.sector)
            self._time.append(self._cur_blk_entry.time)
            self._sequence_list.append((self._sequence, self._time))
        
        self._sequence = []
        self._time = []

    def get_sequence_list(self):
        return self._sequence_list

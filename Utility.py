class Item(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __hash__(self) -> int:
        return hash(self.a) ^ hash(self.b)
    
    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, self.__class__):
            return self.a == __value.a and self.b == __value.b
        else:
            return NotImplemented

    def __repr__(self):
        return "Item({}, {})".format(self.a, self.b)
    

class PairSet(set):
    def insert(self, item):
        if item in self:
            super().remove(item)
        super().add(item)

    def empty(self) -> bool:
        return len(super()) == 0

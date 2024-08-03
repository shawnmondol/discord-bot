from llist import dllist

class MusicQueue:
    def __init__(self):
        self.queue = dllist()
        self.current = None

    def enqueue(self, value):
        self.queue.append(value)

    def dequeue(self):
        if self.queue.first:
            return self.queue.popleft()
        return None

    def peek(self):
        return self.queue.first.value if self.queue.first else None

    def is_empty(self):
        return self.queue.size == 0

    def rewind(self):
        self.current = self.queue.first

    def next(self):
        if self.current:
            value = self.current.value
            self.current = self.current.next
            return value
        return None

    def repeat(self):
        if self.current:
            return self.current.value
        return None

    def reset(self):
        self.current = None
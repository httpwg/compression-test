#!/usr/bin/python
from collections import deque

class KV:
  def __init__(self, key=None, val=None, seq_num=None):
    self.key = key
    self.val = val
    self.seq_num = seq_num

  def ByteSize(self):
    return len(self.val) + len(self.key)

  def __repr__(self):
    return "{(%r, %r) %r}" % \
        (self.key, self.val, self.seq_num)

class LruStorage:
  def __init__(self, max_bytes=None, max_items=None, max_seq_num=None,
               offset=None):
    self.ring = deque()
    self.byte_size = 0
    self.max_items = max_items
    self.max_bytes = max_bytes
    self.max_seq_num = max_seq_num

    self.pop_cb = None
    self.offset = offset
    if offset is None:
      self.offset = 0
    self.seq_num = self.offset

  def __repr__(self):
    return "{%s %r}" % (self.seq_num, self.ring)

  def Reserve(self, byte_size, item_count):
    if self.max_items:
      while len(self.ring) + item_count > self.max_items:
        if not self.PopOne():
          return  0 # can't pop one, nothing more to do.
    if self.max_bytes:
      while self.byte_size + byte_size > self.max_bytes:
        if not self.PopOne():
          return 0 # can't pop one, nothing more to do.
    return 1

  def PopOne(self):
    item = self.ring.popleft()
    self.byte_size -= item.ByteSize()
    #print "POPPING: ", item.seq_num
    if self.pop_cb is not None:
      self.pop_cb(item)
    return 1

  def Store(self, item):
    item_byte_size = item.ByteSize()
    if self.max_bytes and self.byte_size + item_byte_size > self.max_bytes:
      raise MemoryError("max_bytes exceeded")
    if self.max_items and (self.max_items < (len(self.ring) + 1)):
      raise MemoryError("max_items exceeded")
    item.seq_num = self.seq_num
    self.seq_num += 1
    if self.max_seq_num and self.seq_num > self.max_seq_num:
      self.seq_num = self.offset
    self.byte_size += item_byte_size
    self.ring.append(item)

  def Lookup(self, seq_num):
    first_seq_num = self.ring[0].seq_num
    if seq_num < self.offset:
      raise IndexError("Negative indices unsupported: ", seq_num)
    if first_seq_num > seq_num:
      #print "fsn: %d, sn: %d" % (first_seq_num, seq_num)
      if self.max_seq_num:
        #print "a ",;
        lru_idx = (self.max_seq_num - first_seq_num) + seq_num
      else:
        raise IndexError("MaxSeqNum not defined and "
                         "seq_num(%d) < first_seq_num(%d)" %
                         (seq_num, first_seq_num))
    else:
      #print "b ",;
      lru_idx = seq_num - first_seq_num
    #print "Looking up: ", lru_idx
    entry = self.ring[lru_idx]
    return KV(entry.key, entry.val, entry.seq_num)

  def FindKeyValEntries(self, key, val):
    # Looks for key/vals starting from the last entry
    ke = None
    ve = None
    for i in xrange(len(self.ring)-1, 0, -1):
      entry = self.ring[i]
      if entry.key == key:
        ke = entry
        for j in xrange(i, 0, -1):
          entry = self.ring[i]
          if entry.val == val:
            ve = entry
            break
        break
    return (ke, ve)

  def __len__(self):
    return len(self.ring)

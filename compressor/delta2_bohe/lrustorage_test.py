#!/usr/bin/python

from lrustorage import LruStorage
from lrustorage import KV

def TestBasicFunctionality():
  print "TestBasicFunctionality...",
  max_items = 10
  max_byte_size = 7*2*max_items
  s = LruStorage(max_byte_size, max_items)
  key_fmt = "key_%03d"
  val_fmt = "val_%03d"
  for i in xrange(max_items):
    s.Store(KV(key_fmt % i, val_fmt % i))
  assert len(s.ring) == max_items
  assert s.byte_size == max_byte_size
  for i in xrange(max_items):
    entry = s.Lookup(i)
    assert entry.key == key_fmt % i
    assert entry.val == val_fmt % i
    assert entry.seq_num == i
  print "Success!"

def TestMaxItemSize():
  print "TestMaxItemSize...",
  caught_error = 0

  max_items = 10
  max_byte_size = 10000000
  s = LruStorage(max_byte_size, max_items)
  key_fmt = "key_%03d"
  val_fmt = "val_%03d"
  try:
    for i in xrange(max_items+10):
      s.Store(KV(key_fmt % i, val_fmt % i))
  except MemoryError as me:
    caught_error = 1
  if not caught_error:
    print "Failure: Attempted to store too many ITEMS, but no exception"
  else:
    print "Success!"

def TestMaxByteSize():
  print "TestMaxByteSize...",
  caught_error = 0

  max_items = 10
  max_byte_size = 7*2*(max_items - 1)
  s = LruStorage(max_byte_size, max_items)
  key_fmt = "key_%03d"
  val_fmt = "val_%03d"
  try:
    for i in xrange(max_items + 1):
      s.Store(KV(key_fmt % i, val_fmt % i))
  except MemoryError as me:
    if i == max_items - 1:
      caught_error = 1
  if not caught_error:
    print "Failure: Attempted to store too many BYTES, but no exception"
  else:
    print "Success!"

def TestFindKeyValEntries():
  print "TestFindKeyValEntries...",
  caught_error = 0

  max_items = 10
  max_byte_size = 7*2*max_items
  s = LruStorage(max_byte_size, max_items)
  key_fmt = "key_%03d"
  val_fmt = "val_%03d"
  for i in xrange(max_items):
    s.Store(KV(key_fmt % i, val_fmt % i))

  (ke, ve) = s.FindKeyValEntries("key_009", "")
  assert ke.key == "key_009"
  assert ve is None
  (ke, ve) = s.FindKeyValEntries("key_001", "val_001")
  assert ke.key == "key_001"
  assert ve.key == "key_001"
  assert ve.val == "val_001"
  print "Success!"

def TestPopOne():
  print "TestPopOne...",
  caught_error = 0

  max_items = 10
  max_byte_size = 7*2*max_items
  s = LruStorage(max_byte_size, max_items)
  key_fmt = "key_%03d"
  val_fmt = "val_%03d"
  for i in xrange(max_items):
    s.Store(KV(key_fmt % i, val_fmt % i))

  assert s.Lookup(0).key == key_fmt % 0

  for i in xrange(0, max_items):
    entry = s.Lookup(i) # this should work, of course.
    s.PopOne()
    try:
      s.Lookup(i)
    except IndexError as ie:
      caught_error = 1
    if not caught_error:
      print s.ring
      print s.Lookup(i)
      print "Failure: PopOne() didn't pop the first element"
      return

  assert s.byte_size == 0
  assert len(s.ring) == 0

  caught_error = 0
  try:
    s.PopOne()
  except:
    caught_error = 1
    pass
  if not caught_error:
    print "Did PopOne() with empty LruStorage, and got no error!?"
    return

  print "Success!"

def TestReserve():
  print "TestReserve...",
  max_items = 10
  max_byte_size = 1000
  s = LruStorage(max_byte_size, max_items)
  key_fmt = "key_%06d"
  val_fmt = "val_%06d"
  for i in xrange(max_items + 10):
    if i < max_items:
      kv = KV(key_fmt % i, val_fmt % i)
      s.Store(kv)
    else:
      try:
        kv = KV(key_fmt % i, val_fmt % i)
        s.Store(kv)
        print "This shouldn't have worked. Error."
        return
      except MemoryError as me:
        s.Reserve(kv.ByteSize(), 1)
        kv = KV(key_fmt % i, val_fmt % i)
        s.Store(kv)

  s = LruStorage(20, max_items)
  s.Store(KV("12345", "67890"))
  s.Store(KV("12345", "67890"))
  try:
    s.Store(KV("12345", "678901"))
    print "This shouldn't have worked. Error."
    return
  except MemoryError as me:
    s.Reserve(11,1)
    s.Store(KV("12345", "678901"))
    assert len(s.ring) == 1
  print "Success!"


def TestRollOver():
  print "TestRollOver...",
  max_items = 64
  max_seq_num = 64
  max_byte_size = (6+4)*2*max_items
  s = LruStorage(max_byte_size, max_items, max_seq_num)
  key_fmt = "key_%06d"
  val_fmt = "val_%06d"
  for i in xrange(max_items + max_items/2):
    kv = KV(key_fmt % i, val_fmt % i)
    s.Reserve(kv.ByteSize(), 1)
    s.Store(kv)
  for i in xrange(max_items/2, max_items + max_items/2):
    key_str = key_fmt % i
    s.Lookup(i % max_seq_num).key == key_str
  print "Success!"

def main():
  TestBasicFunctionality()
  TestMaxItemSize()
  TestMaxByteSize()
  TestFindKeyValEntries()
  TestPopOne()
  TestReserve()
  TestRollOver()

main()


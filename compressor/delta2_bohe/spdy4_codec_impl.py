#!/usr/bin/python

# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import string
import struct

from bit_bucket import BitBucket
from collections import defaultdict
from collections import deque
import common_utils
from huffman import Huffman
from optparse import OptionParser
from ..spdy_dictionary import spdy_dict
from word_freak import WordFreak
import lrustorage
import bohe

options = {}

g_default_kvs = [
    ('date', ''),
    (':scheme', 'https'),
    (':method', 'get'),
    (':path', '/'),
    (':host', ''),
    ('cookie', ''),
    (':status', '200'),
    (':status-text', 'OK'),
    (':version', '1.1'),
    ('accept', ''),
    ('accept-charset', ''),
    ('accept-encoding', ''),
    ('accept-language', ''),
    ('accept-ranges', ''),
    ('allow', ''),
    ('authorizations', ''),
    ('cache-control', ''),
    ('content-base', ''),
    ('content-encoding', ''),
    ('content-length', ''),
    ('content-location', ''),
    ('content-md5', ''),
    ('content-range', ''),
    ('content-type', ''),
    ('etag', ''),
    ('expect', ''),
    ('expires', ''),
    ('from', ''),
    ('if-match', ''),
    ('if-modified-since', ''),
    ('if-none-match', ''),
    ('if-range', ''),
    ('if-unmodified-since', ''),
    ('last-modified', ''),
    ('location', ''),
    ('max-forwards', ''),
    ('origin', ''),
    ('pragma', ''),
    ('proxy-authenticate', ''),
    ('proxy-authorization', ''),
    ('range', ''),
    ('referer', ''),
    ('retry-after', ''),
    ('server', ''),
    ('set-cookie', ''),
    ('status', ''),
    ('te', ''),
    ('trailer', ''),
    ('transfer-encoding', ''),
    ('upgrade', ''),
    ('user-agent', ''),
    ('user-agent', ''),
    ('vary', ''),
    ('via', ''),
    ('warning', ''),
    ('www-authenticate', ''),
    ('access-control-allow-origin', ''),
    ('content-disposition', ''),
    ('get-dictionary', ''),
    ('p3p', ''),
    ('x-content-type-options', ''),
    ('x-frame-options', ''),
    ('x-powered-by', ''),
    ('x-xss-protection', ''),
    ('connection', 'keep-alive'),
]

# Performance is a non-goal for this code.

# TODO:try var-int encoding for indices, or use huffman-coding on the indices
# TODO:use a separate huffman encoding for cookies, and possibly for path
# TODO:interpret cookies as binary instead of base-64, does it reduce entropy?
# TODO:make index renumbering useful so things which are often used together
#      have near indices, or remove it as not worth the cost/complexity
# TODO:use other mechanisms other than LRU to perform entry expiry
# TODO:use canonical huffman codes, like the c++ version
# TODO:use huffman coding on the operation type. Clones and toggles are by far
#      the most common operations.
# TODO:use huffman coding on the operation count. Small counts are far more
#      common than large counts. Alternatively, simply use a smaller fixed-size.
# TODO:modify the huffman-coding to always emit a code starting with 1 so that
#      we can differentiate easily between strings that are huffman encoded or
#      strings which are not huffman encoded by examining the first bit.
#      Alternately, define different opcodes for the various variations.
# TODO:modify the string packing/unpacking to indicate whether the following
#      string is huffman-encoded or not. Assuming 7-bit ascii (which is
#      something to be discussed, this can be accomplished by adding a single
#      bit before huffman-encoded strings (with value 1). There are other ways
#      of accomplishing the same thing, e.g. using different operation opcodes
#      to indicate whether the string parameters in that operation are huffman
#      encoded.

# Note: Huffman coding is used here instead of range-coding or
# arithmetic-coding because of its relative CPU efficiency and because it is
# fairly well known (though the canonical huffman code is a bit less well
# known, it is still better known than most other codings)


###### BEGIN IMPORTANT PARAMS ######
#  THESE PARAMETERS ARE IMPORTANT

# If strings_use_eof is true, then the bitlen is not necessary, and possibly
#  detrimental, as it caps the maximum length of any particular string.
string_length_field_bitlen = 0

# If strings_use_eof is false, however, then string_length_field_bitlen
#  MUST be >0
strings_use_eof = 1

# If strings_padded_to_byte_boundary is true, then it is potentially faster
# (in an optimized implementation) to decode/encode, at the expense of some
# compression efficiency.
strings_padded_to_byte_boundary = 1

# if strings_use_huffman is false, then strings will not be encoded with
# huffman encoding
strings_use_huffman = 1

###### END IMPORTANT PARAMS ######


def UnpackInt(input, bitlen, huff):
  """
  Reads an int from an input BitBucket and returns it.

  'bitlen' is between 1 and 32 (inclusive), and represents the number of bits
  to be read and interpreted as the int.

  'huff' is unused.
  """
  raw_input = input.GetBits(bitlen)[0]
  rshift = 0
  if bitlen <=8:
    arg = '%c%c%c%c' % (0,0, 0,raw_input[0])
    rshift = 8 - bitlen
  elif bitlen <=16:
    arg = '%c%c%c%c' % (0,0, raw_input[0], raw_input[1])
    rshift = 16 - bitlen
  elif bitlen <=24:
    arg = '%c%c%c%c' % (0,raw_input[0], raw_input[1], raw_input[2])
    rshift = 24 - bitlen
  else:
    arg = '%c%c%c%c' % (raw_input[0], raw_input[1], raw_input[2], raw_input[3])
    rshift = 32 - bitlen
  retval = (struct.unpack('>L', arg)[0] >> rshift)
  return retval

def UnpackStr(input, params, huff):
  """
  Reads a string from an input BitBucket and returns it.

  'input' is a BitBucket containing the data to be interpreted as a string.

  'params' is (bitlen_size, use_eof, pad_to_byte_boundary, use_huffman)

  'bitlen_size' indicates the size of the length field. A size of 0 is valid IFF
  'use_eof' is true.

  'use_eof' indicates that an EOF character will be used (for ascii strings,
  this will be a null. For huffman-encoded strings, this will be the specific
  to that huffman encoding).

  If 'pad_to_byte_boundary' is true, then the 'bitlen_size' parameter
  represents bits of size, else 'bitlen_size' represents bytes.


  if 'use_huffman' is false, then the string is not huffman-encoded.

  If 'huff' is None, then the string is not huffman-encoded. If 'huff' is not
  None, then it must be a Huffman compatible object which is used to do huffman
  decoding.
  """
  (bitlen_size, use_eof, pad_to_byte_boundary, use_huffman) = params
  if not use_huffman:
    huff = None
  if not use_eof and not bitlen_size:
    # without either a bitlen size or an EOF, we can't know when the string ends
    # having both is certainly fine, however.
    raise StandardError()
  if bitlen_size:
    bitlen = UnpackInt(input, bitlen_size, huff)
    if huff:
      retval = huff.DecodeFromBB(input, use_eof, bitlen)
    else:
      retval = input.GetBits(bitlen)[0]
  else:  # bitlen_size == 0
    if huff:
      retval = huff.DecodeFromBB(input, use_eof, 0)
    else:
      retval = []
      while True:
        c = input.GetBits8()
        retval.append(c)
        if c == 0:
          break
  if pad_to_byte_boundary:
    input.AdvanceToByteBoundary()
  retval = common_utils.ListToStr(retval)
  return retval

# this assumes the bits are near the LSB, but must be packed to be close to MSB
def PackInt(data, bitlen, val, huff):
  """ Packs an int of up to 32 bits, as specified by the 'bitlen' parameter into
  the BitBucket object 'data'.
  'data' the BitBucket object into which the int is written
  'bitlen' the number of bits used for the int
  'val' the value to be packed into data (limited by bitlen)
        If val is larger than 'bitlen', the bits near the LSB are packed.
  'huff' is unused.
  """
  if bitlen <= 0 or bitlen > 32 or val != (val & ~(0x1 << bitlen)):
    print 'bitlen: ', bitlen, ' val: ', val
    raise StandardError()
  if bitlen <= 8:
    tmp_val = struct.pack('>B', val << (8 - bitlen))
  elif bitlen <= 16:
    tmp_val = struct.pack('>H', val << (16 - bitlen))
  elif bitlen <= 24:
    tmp_val = struct.pack('>L', val << (24 - bitlen))[1:]
  else:
    tmp_val = struct.pack('>L', val << (32 - bitlen))
  data.StoreBits( (common_utils.StrToList(tmp_val), bitlen) )

def PackStr(data, params, val, huff):
  """
  Packs a string into the output BitBucket ('data').
  'data' is the BitBucket into which the string will be written.
  'params' is (bitlen_size, use_eof, pad_to_byte_boundary, use_huffman)
  bitlen_size - between 0 and 32 bits. It can be zero IFF 'use_eof' is true
  use_eof - if true, the string is encoded with an EOF character. When
            use_huffman is false, this character is '\0', but when
            use_huffman is true, this character is determined by the encoder
  pad_to_byte_boundary - if true, then enough bits are written to ensure that
                         the data ends on a byte boundary.
  'val' is the string to be packed
  'huff' is the Huffman object to be used when doing huffman encoding.
  """
  (bitlen_size, use_eof, pad_to_byte_boundary, use_huffman) = params
  # if eof, then don't technically need bitlen at all...
  if not use_huffman:
    huff = None

  if not use_eof and not bitlen_size:
    # without either a bitlen size or an EOF, we can't know when the string ends
    # having both is certainly fine, however.
    raise StandardError()
  val_as_list = common_utils.StrToList(val)
  len_in_bits = len(val) * 8
  if huff:
    (val_as_list, len_in_bits) = huff.Encode(val_as_list, use_eof)
    if pad_to_byte_boundary:
      len_in_bits = len(val_as_list) *8
  if bitlen_size:
    PackInt(data, bitlen_size, len_in_bits, huff)
  data.StoreBits( (val_as_list, len_in_bits) )

str_pack_params = (string_length_field_bitlen, strings_use_eof,
                   strings_padded_to_byte_boundary, strings_use_huffman)
# This is the list of things to do for each fieldtype we may be packing.
# the first param is what is passed to the pack/unpack function.
# the second and third params are the packing and unpacking functions,
# respectively.
packing_instructions = {
  'opcode'      : (  8,             PackInt, UnpackInt),
  'index'       : ( 16,             PackInt, UnpackInt),
  'index_start' : ( 16,             PackInt, UnpackInt),
  'key_idx'     : ( 16,             PackInt, UnpackInt),
  'val'         : (str_pack_params, PackStr, UnpackStr),
  'key'         : (str_pack_params, PackStr, UnpackStr),
}

def PackOps(data, packing_instructions, ops, huff, group_id):
  """ Packs (i.e. renders into wire-format) the operations in 'ops' into the
  BitBucket 'data', using the 'packing_instructions' and possibly the Huffman
  encoder 'huff'
  """
  seder = Spdy4SeDer()
  data.StoreBits(seder.SerializeInstructions(ops, packing_instructions,
                                             huff, 1234, group_id, True))

def UnpackOps(data, packing_instructions, huff):
  """
  Unpacks wire-formatted ops into an in-memory representation
  """
  seder = Spdy4SeDer()
  return seder.DeserializeInstructions(data, packing_instructions, huff)

# The order in which to format and pack operations.
packing_order = ['opcode',
                 'index',
                 'index_start',
                 'key_idx',
                 'key',
                 'val',
                 ]

# opcode-name: opcode-value list-of-fields-for-opcode
opcodes = {
    'toggl': (0x1, 'index'),
    'trang': (0x2, 'index', 'index_start'),
    'clone': (0x3,                         'key_idx', 'val'),
    'kvsto': (0x4,          'key',                    'val'),
    'eref' : (0x5,          'key',                    'val'),

    #'etoggl': (0x5, 'index'),
    #'etrang': (0x6, 'index', 'index_start'),
    #'eclone': (0x7,                         'key_idx', 'val'),
    #'ekvsto': (0x8,          'key',                    'val'),
    }

# an inverse dict of opcode-val: opcode-name list-of-fields-for-opcode
opcode_to_op = {}
for (key, val) in opcodes.iteritems():
  opcode_to_op[val[0]] = [key] + list(val[1:])

def OpcodeToVal(opcode_name):
  """ Gets the opcode-value for an opcode-name"""
  return opcodes[opcode_name][0]

def FormatOp(op):
  """ Pretty-prints an op to a string for easy human consumption"""
  order = packing_order
  outp = ['{']
  inp = []
  for key in order:
    if key in op and key != 'opcode':
      inp.append("'%s': % 5s" % (key, repr(op[key])))
    if key in op and key == 'opcode':
      inp.append("'%s': % 5s" % (key, repr(op[key]).ljust(7)))
  for (key, val) in op.iteritems():
    if key in order:
      continue
    inp.append("'%s': %s" % (key, repr(op[key])))
  outp.append(', '.join(inp))
  outp.append('}')
  return ''.join(outp)

def FormatOps(ops, prefix=None):
  """ Pretty-prints an operation or list of operations for easy human
  consumption"""
  if prefix is None:
    prefix = ''
  if isinstance(ops, list):
    for op in ops:
      print prefix,
      print FormatOp(op)
    return
  for optype in ops.iterkeys():
    for op in ops[optype]:
      print prefix,
      print FormatOp(op)


class Spdy4SeDer(object):  # serializer deserializer
  """
  A class which serializes into and/or deserializes from SPDY4 wire format
  """
  def PreProcessToggles(self, instructions):
    """
    Examines the 'toggl' operations in 'instructions' and computes the
    'trang' and remnant 'toggle' operations, returning them as:
    (output_toggles, output_toggle_ranges)
    """
    toggles = instructions['toggl']
    toggles.sort()
    ot = []
    otr = []
    for toggle in toggles:
      idx = toggle['index']
      if otr and idx - otr[-1]['index'] == 1:
        otr[-1]['index'] = idx
      elif ot and idx - ot[-1]['index'] == 1:
        otr.append(ot.pop())
        otr[-1]['index_start'] = otr[-1]['index']
        otr[-1]['index'] = idx
        otr[-1]['opcode'] = 'trang'
      else:
        ot.append(toggle)
    return [ot, otr]

  def OutputOps(self, packing_instructions, huff, data, ops, opcode):
    """
    formats ops (all of type represented by opcode) into wire-format, and
    stores them into the BitBucket represented by 'data'

    'data' the bitbucket into which everything is stored
    'packing_instructions' the isntructions on how to pack fields
    'huff' a huffman object possibly used for string encoding
    'ops' the operations to be encoded into spdy4 wire format and stored.
    'opcode' the type of all of the ops.

    The general format of such is:
    | opcode-type | num-opcodes | list-of-operations
    where num-opcodes cannot exceed 256, thus the function may output
    a number of such sequences.
    """
    if not ops:
      return;
    ops_idx = 0
    ops_len = len(ops)
    while ops_len > ops_idx:
      ops_to_go = ops_len - ops_idx
      iteration_end = min(ops_to_go, 256) + ops_idx
      data.StoreBits8(OpcodeToVal(opcode))
      data.StoreBits8(min(256, ops_to_go) - 1)
      orig_idx = ops_idx
      for i in xrange(ops_to_go):
        try:
          self.WriteOpData(data, ops[orig_idx + i], huff)
        except:
          print opcode, ops
          raise
        ops_idx += 1

  def WriteOpData(self, data, op, huff):
    """
    A helper function for OutputOps which does the packing for
    the operation's fields.
    """
    # turn off huffman coding for this operation.. we're using a binary encoded value
    if 'huff' in op and not op['huff']:
      huff = None
    for field_name in packing_order:
      if not field_name in op:
        continue
      if field_name == 'opcode':
        continue
      (params, pack_fn, _) = packing_instructions[field_name]
      val = op[field_name]
      try:
        pack_fn(data, params, val, huff)
      except:
        print field_name, data, params, val
        raise

  def WriteControlFrameStreamId(self, data, stream_id):
    if (stream_id & 0x80000000):
      abort()
    data.StoreBits32(0x80000000 | stream_id)

  def WriteControlFrameBoilerplate(self,
      data,
      frame_len,
      flags,
      stream_id,
      group_id,
      frame_type):
    """ Writes the frame-length, flags, stream-id, and frame-type
    in SPDY4 format into the bit-bucket represented bt 'data'"""
    data.StoreBits16(frame_len)
    data.StoreBits8(flags)
    #data.StoreBits32(stream_id)
    self.WriteControlFrameStreamId(data, stream_id)
    data.StoreBits8(frame_type)
    data.StoreBits8(group_id)

  def SerializeInstructions(self,
      ops,
      packing_instructions,
      huff,
      stream_id,
      group_id,
      end_of_frame):
    """ Serializes a set of instructions possibly containing many different
    type of opcodes into SPDY4 wire format, discovers the resultant length,
    computes the appropriate SPDY4 boilerplate, and then returns this
    in a new BitBucket
    """
    #print 'SerializeInstructions\n', ops
    (ot, otr) = self.PreProcessToggles(ops)

    payload_bb = BitBucket()
    self.OutputOps(packing_instructions, huff, payload_bb, ot, 'toggl')
    self.OutputOps(packing_instructions, huff, payload_bb, otr, 'trang')
    self.OutputOps(packing_instructions, huff, payload_bb, ops['clone'],'clone')
    self.OutputOps(packing_instructions, huff, payload_bb, ops['kvsto'],'kvsto')
    self.OutputOps(packing_instructions, huff, payload_bb, ops['eref'], 'eref')

    (payload, payload_len) = payload_bb.GetAllBits()
    payload_len = (payload_len + 7) / 8  # partial bytes are counted as full
    frame_bb = BitBucket()
    self.WriteControlFrameBoilerplate(frame_bb, 0, 0, 0, group_id, 0)
    boilerplate_length = frame_bb.BytesOfStorage()
    frame_bb = BitBucket()
    overall_bb = BitBucket()
    bytes_allowed = 2**16 - boilerplate_length
    while True:
      #print 'payload_len: ', payload_len
      bytes_to_consume = min(payload_len, bytes_allowed)
      #print 'bytes_to_consume: ', bytes_to_consume
      end_of_frame = (bytes_to_consume <= payload_len)
      #print 'end_of_Frame: ', end_of_frame
      self.WriteControlFrameBoilerplate(overall_bb, bytes_to_consume,
                                        end_of_frame, stream_id, group_id, 0x8)
      overall_bb.StoreBits( (payload, bytes_to_consume*8))
      payload = payload[bytes_to_consume:]
      payload_len -= bytes_allowed
      if payload_len <= 0:
        break
    return overall_bb.GetAllBits()

  def DeserializeInstructions(self, frame, packing_instructions, huff):
    """ Takes SPDY4 wire-format data and de-serializes it into in-memory
    operations
    It returns these operations.
    """
    ops = []
    bb = BitBucket()
    bb.StoreBits(frame.GetAllBits())
    flags = 0
    #print 'DeserializeInstructions'
    while flags == 0:
      frame_len = bb.GetBits16() * 8
      #print 'frame_len: ', frame_len
      flags = bb.GetBits8()
      #print 'flags: ', flags
      stream_id = bb.GetBits32()
      #print 'stream_id: ', stream_id
      frame_type = bb.GetBits8()
      #print 'frame_type: ', frame_type
      group_id = bb.GetBits8()
      #print 'group_id: ', group_id
      while frame_len > 16:  # 16 bits minimum for the opcode + count...
        bits_remaining_at_start = bb.BitsRemaining()
        opcode_val = bb.GetBits8()
        #print 'opcode_val: ', opcode_val
        op_count = bb.GetBits8() + 1
        #print 'op_count: ', op_count
        opcode_description = opcode_to_op[opcode_val]
        opcode = opcode_description[0]
        fields = opcode_description[1:]
        for i in xrange(op_count):
          op = {'opcode': opcode}
          for field_name in packing_order:
            if not field_name in fields:
              continue
            (params, _, unpack_fn) = packing_instructions[field_name]
            val = unpack_fn(bb, params, huff)
            #print val
            op[field_name] = val
            #print "BitsRemaining: %d (%d)" % (bb.BitsRemaining(), bb.BitsRemaining() % 8)
          #print "Deser %d" % (bb.NumBits() - bb.BitsRemaining())
          #print op
          ops.append(op)
        bits_consumed = (bits_remaining_at_start - bb.BitsRemaining())
        #if not bits_consumed % 8 == 0:
        #  print "somehow didn't consume whole bytes..."
        #  print "Bits consumed: %d (%d)" % (bits_consumed, bits_consumed % 8)
        #  raise StandardError()
        frame_len -= bits_consumed
    #print 'ops: ', ops
    return (group_id, ops)

class HeaderGroup(object):
  """ A HeaderGroup is a list of ValueEntries (VEs) which are the key-values to
  be instantiated as a header frame """
  def __init__(self, storage):
    self.hg_store = dict()
    self.generation = 0
    self.storage = storage

  def HasKVAndTouchIfTrue(self, key, val):
    for idx in self.hg_store.keys():
      e = self.storage.LookupFromIdx(idx)
      if e.key == key and e.val == val:
        self.TouchEntry(idx)
        return 1
    return 0

  def Empty(self):
    return not self.hg_store

  def IncrementGeneration(self):
    self.generation += 1

  def HasEntry(self, v_idx):
    retval = v_idx in self.hg_store.keys()
    #if retval:
    #  print "\t\t\t", v_idx, "is already in self.hg_store"
    #else:
    #  print "\t\t\t", v_idx, " is not in self.hg_store"
    return retval

  def TouchEntry(self, v_idx):
    if v_idx is None:
      raise StandardError()
    self.hg_store[v_idx] = self.generation
    #print "\t\t\tTouching: %r: %r" % (v_idx, self.generation)

  def RemoveEntry(self, v_idx):
    try:
      del self.hg_store[v_idx]
    except KeyError:
      pass

  def FindOldEntries(self):
    def NotCurrent(x):
      return x != self.generation
    retval = [e for (e,g) in self.hg_store.iteritems() if NotCurrent(g)]
    return retval

  def GetIdxs(self):
    return self.hg_store.keys()

  def Toggle(self, v_idx):
    if v_idx is None:
      raise StandardError()
    try:
      del self.hg_store[v_idx]
    except KeyError:
      if v_idx in self.hg_store:
        raise StandardError()
      self.hg_store[v_idx] = self.generation

  def __repr__(self):
    return repr(self.hg_store)

class Storage(object):
  def __init__(self):
    self.static_storage = lrustorage.LruStorage()
    for k,v in g_default_kvs:
      self.static_storage.Store(lrustorage.KV(k,v))
    self.lru_storage = lrustorage.LruStorage(16*1024,
                                             1024,
                                             2**16,
                                             len(self.static_storage))

  def SetRemoveValCB(self, remove_val_cb):
    self.lru_storage.pop_cb = remove_val_cb

  def LookupFromIdx(self, entry_seqnum):
    if entry_seqnum < len(self.static_storage):
      return self.static_storage.Lookup(entry_seqnum)
    return self.lru_storage.Lookup(entry_seqnum)

  def InsertVal(self, entry):
    self.lru_storage.Reserve(entry.ByteSize(), 1)
    self.lru_storage.Store(entry)
    return self.lru_storage.ring[-1].seq_num

  def MoveToHeadOfLRU(self, entry):
    self.InsertVal(entry)

  def FindEntryIdx(self, key, val):
    retval = [None, None]
    (ke, ve) = self.lru_storage.FindKeyValEntries(key, val)
    if ke:
      retval[0] = ke.seq_num
      if ve:
        retval[1] = ve.seq_num
      else:
        (__, ve) = self.static_storage.FindKeyValEntries(key, val)
        if ve:
          retval[1] = ve.seq_num
    else:
      (ke, ve) = self.static_storage.FindKeyValEntries(key, val)
      if ke:
        retval[0] = ke.seq_num
      if ve:
        retval[1] = ve.seq_num
    #print "\t\tLooking for(%s, %s): found at: (%r, %r)" % \
    #    (key, val, retval[0], retval[1])
    return retval

class Spdy4CoDe(object):
  def __init__(self, is_request=True):
    self.header_groups = {}
    self.huffman_table = None
    self.wf = WordFreak()
    self.storage = Storage()
    self.is_request = is_request
    
    def RemoveVIdxFromAllHeaderGroups(entry):
      v_idx = entry.seq_num
      #print "Removing %d from all!" % v_idx
      to_be_removed = []
      for group_id, header_group in self.header_groups.iteritems():
        #print "Removing %d from hg %d" % (ve['lru_idx'], group_id)
        header_group.RemoveEntry(v_idx)
        if header_group.Empty():
          to_be_removed.append(group_id)
      for group_id in to_be_removed:
        #print "Deleted group_id: %d" % group_id
        del self.header_groups[group_id]
    self.storage.SetRemoveValCB(RemoveVIdxFromAllHeaderGroups)

  def OpsToRealOps(self, in_ops, header_group):
    """ Packs in-memory format operations into wire format"""
    data = BitBucket()
    #print FormatOps(in_ops)
    PackOps(data, packing_instructions, in_ops, self.huffman_table, header_group)
    return common_utils.ListToStr(data.GetAllBits()[0])

  def RealOpsToOps(self, realops):
    """ Unpacks wire format operations into in-memory format"""
    bb = BitBucket()
    bb.StoreBits((common_utils.StrToList(realops), len(realops)*8))
    return UnpackOps(bb, packing_instructions, self.huffman_table)

  def Compress(self, realops):
    """ basically does nothing"""
    ba = ''.join(realops)
    return ba

  def Decompress(self, op_blob):
    """ basically does nothing"""
    return op_blob

  def MakeToggl(self, index):
    return {'opcode': 'toggl', 'index': index}

  def MakeKvsto(self, key, val, use_huffman=False):
    return {'opcode': 'kvsto', 'val': val, 'key': key, 'huff': use_huffman}

  def MakeTclon(self, key, val):
    return {'opcode': 'tclon', 'val': val, 'key': key}

  def MakeClone(self, key_idx, val, use_huffman=False):
    return {'opcode': 'clone', 'val': val, 'key_idx': key_idx, 'huff': use_huffman}

  def MakeERef(self, key, value, use_huffman=False):
    return {'opcode': 'eref', 'key': key, 'val': value, 'huff': use_huffman}

  def FindOrMakeHeaderGroup(self, group_id):
    try:
      return self.header_groups[group_id]
    except KeyError:
      self.header_groups[group_id] = HeaderGroup(self.storage)
      return self.header_groups[group_id]

  def TouchHeaderGroupEntry(self, group_id, v_idx):
    if v_idx is None:
      raise StandardError()
    header_group = self.FindOrMakeHeaderGroup(group_id)
    #print "\t\t\ttouching/adding idx: %r in group: %d" % (v_idx, group_id)
    header_group.TouchEntry(v_idx)

  def VEInHeaderGroup(self, group_id, v_idx):
    return self.header_groups[group_id].HasEntry(v_idx)

  def DiscoverTurnOffs(self, group_id, instructions):
    """ Discovers the elements in the header-group which are not current, and
    thus should be removed from the header group (i.e. turned off)
    """
    toggles_off = []
    header_group = self.FindOrMakeHeaderGroup(group_id)
    for v_idx in header_group.FindOldEntries():
      #print "\t\t*** toggl (OFF): ", v_idx
      toggles_off.append(self.MakeToggl(v_idx))
    return toggles_off

  def AdjustHeaderGroupEntries(self, group_id):
    """ Moves elements which have been referenced/modified to the head of the LRU
    and possibly renumbers them"""
    header_group = self.header_groups[group_id]
    try:
      items_to_move = []
      for v_idx in sorted(header_group.GetIdxs()):
        items_to_move.append(self.storage.LookupFromIdx(v_idx))
      for item in items_to_move:
        self.storage.MoveToHeadOfLRU(item)
    except:
      print header_group
      raise

  def ExecuteInstructionsExceptERefs(self, group_id, instructions):
    if 'trang' in instructions:
      raise StandardError()
    for op in instructions['toggl']:
      self.ExecuteOp(group_id, op)
    translated_clones = []
    for op in instructions['clone']:
      key_idx = op['key_idx']
      val = op['val']
      ke = self.storage.LookupFromIdx(key_idx)
      if ke is None:
         print "key_idx: ", key_idx, " and ke is None. crap."
         print self.storage.lru
         raise StandardError()
      tclon = self.MakeTclon(ke.key, val)
      #print "\t\t\t translated clone %d to tclon %r" % (key_idx, tclon)
      translated_clones.append(tclon)
    for op in translated_clones:
      self.ExecuteOp(group_id, op)
    for op in instructions['kvsto']:
      self.ExecuteOp(group_id, op)

  def ProcessKV(self, key, val, group_id, instructions):
    """ Comes up with the appropriate operation for the key, value, and adds
    it into 'instructions'"""
    use_huffman = not key in bohe.ENCODERS
    #print "\tkey: %s, val: %s" % (key, val)
    if self.header_groups[group_id].HasKVAndTouchIfTrue(key, val):
      #print "\t\tAlready in HG and touched the entry. Nothing else to do."
      return
    
    (k_idx, v_idx) = self.storage.FindEntryIdx(key, val)
    #if v_idx is not None:
    #  print "\t\tFound val at idx: ", v_idx
    #elif k_idx is not None:
    #  print "\t\tFound key at idx: ", k_idx
    #else:
    #  print "\t\tNothing matched key or value"
    if v_idx is not None:
      if not self.VEInHeaderGroup(group_id, v_idx):
        #print "\t\t**** toggle for idx: ", v_idx
        op = self.MakeToggl(v_idx)
        instructions['toggl'].append(op)
      else:
        #print "\t\t**** Nothing to do"
        self.TouchHeaderGroupEntry(group_id, v_idx)
    elif k_idx is not None:
      #print "\t\t**** clone: %r %s" % (k_idx, self.storage.LookupFromIdx(k_idx).key)
      op = self.MakeClone(k_idx, val, use_huffman)
      instructions['clone'].append(op)
    else: # kvsto or tclon
      #print "\t\t**** kvsto: ", key, val
      op = self.MakeKvsto(key, val, use_huffman)
      instructions['kvsto'].append(op)

  def MakeOperations(self, headers, group_id):
    """ Computes the entire set of operations necessary to encode the 'headers'
    for header-group 'group_id'
    """
    instructions = {'toggl': [], 'clone': [], 'kvsto': [], 'eref': []}
    incremented_keys = []
    #self.storage.PinLRU()
    self.FindOrMakeHeaderGroup(group_id)  # make the header group if necessary
    #print '#' * 80
    #print '\n'.join(["%s: %s"%(k,v) for k,v in headers.iteritems()])
    #print "LRU(after Make+Execute) ", self.storage.lru_storage.ring
    #print "HG:", self.header_groups[group_id]
    for k,v in headers.iteritems():
      if k == 'cookie':
        splitvals = [x.lstrip(' ') for x in v.split(';')]
        splitvals.sort()
        for splitval in splitvals:
          self.ProcessKV(k, bohe.encode(k,splitval,self.is_request), group_id, instructions)
      else:
        self.ProcessKV(k, bohe.encode(k,v,self.is_request), group_id, instructions)

    #print "EXECUTING NON-TURNOFFS"
    self.ExecuteInstructionsExceptERefs(group_id, instructions)
    #print "COMPUTING TURNOFFS"
    turn_offs = self.DiscoverTurnOffs(group_id, instructions)
    for op in turn_offs:
      self.ExecuteOp(group_id, op)
    instructions['toggl'].extend(turn_offs)
    #print "DONE COMPUTING INSTRUCTIONS"
    #print FormatOps(instructions)
    #print "LRU(after Make+Execute) ", self.storage.lru_storage
    #self.storage.UnPinLRU()
    self.header_groups[group_id].IncrementGeneration()
    self.AdjustHeaderGroupEntries(group_id)
    #FormatOps(instructions, 'MO\t')
    return instructions

  def RealOpsToOpAndExecute(self, realops):
    """ Deserializes from SPDY4 wire format and executes the operations"""
    (group_id, ops) = self.RealOpsToOps(realops)
    #FormatOps(ops,'ROTOAE\t')
    #self.storage.PinLRU()
    self.ExecuteOps(ops, group_id)
    #self.storage.UnPinLRU()
    return (group_id, ops)

  def ExecuteOps(self, ops, group_id, ephemereal_headers=None):
    """ Executes a list of operations"""
    self.FindOrMakeHeaderGroup(group_id)  # make the header group if necessary
    if ephemereal_headers is None:
      ephemereal_headers = {}
    translated_clones = []
    for op in ops:
      if op['opcode'] == 'clone':
        key_idx = op['key_idx']
        val = op['val']
        ke = self.storage.LookupFromIdx(key_idx)
        tclon = self.MakeTclon(ke.key, val)
        #print "\t\t\t translated clone %d to tclon %r" % (key_idx, tclon)
        translated_clones.append(tclon)
    for op in translated_clones:
      self.ExecuteOp(group_id, op, ephemereal_headers)
    for op in ops:
      if op['opcode'] == 'clone':
        continue
      self.ExecuteOp(group_id, op, ephemereal_headers)
    #print 'DONE'

  def ExecuteToggle(self, group_id, idx):
    #print "\t\t!!!   toggl: ", idx, self.storage.LookupFromIdx(idx)
    self.header_groups[group_id].Toggle(idx)

  def ExecuteOp(self, group_id, op, ephemereal_headers=None):
    """ Executes a single operation """
    #print 'Executing: ', FormatOp(op)
    opcode = op['opcode']
    if opcode == 'toggl':
      # Toggl - toggle visibility
      idx = op['index']
      self.ExecuteToggle(group_id, idx)
    elif opcode == 'trang':
      # Trang - toggles visibility for a range of indices
      for idx in xrange(op['index_start'], op['index']+1):
        self.ExecuteToggle(group_id, idx)
    elif opcode == 'clone':
      print "This should have been translated to a tclon before execution began"
      raise StandardError()
    elif opcode == 'kvsto' or opcode == 'tclon':
      # kvsto - store key,value
      #print "\t\t!!! %s %s %s" % (opcode, op['key'], op['val'])
      v_idx = self.storage.InsertVal(lrustorage.KV(op['key'], op['val']))
      self.TouchHeaderGroupEntry(group_id, v_idx)
    elif opcode == 'eref' and ephemereal_headers is not None:
      ephemereal_headers[op['key']] = op['val']

  def GenerateAllHeaders(self, group_id):
    """ Given a group-id, generates the set of headers currently associated
    with that header group, and returns them.
    """
    headers = {}
    header_group = self.header_groups[group_id]
    #print "GenerateAllheaders HeaderGroup: ", header_group

    try:
      for v_idx in sorted(header_group.GetIdxs()):
        ve = self.storage.LookupFromIdx(v_idx)
        key = ve.key
        val = ve.val
        if key in headers:
          headers[key] = headers[key] + '\0' + val
        else:
          headers[key] = val
    except:
      print repr(header_group)
      raise
    if 'cookie' in headers:
      headers['cookie'] = headers['cookie'].replace('\0', '; ')
    self.AdjustHeaderGroupEntries(group_id)
    return headers


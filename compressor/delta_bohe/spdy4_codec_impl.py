#!/usr/bin/python

# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import string
import struct
import bohe

from bit_bucket import BitBucket
from collections import defaultdict
from collections import deque
from common_utils import *
#from common_utils import IDStore
from huffman import Huffman
from optparse import OptionParser
from ..spdy_dictionary import spdy_dict
from word_freak import WordFreak

options = {}

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
  retval = ListToStr(retval)
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
  data.StoreBits( (StrToList(tmp_val), bitlen) )

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
  val_as_list = StrToList(val)
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

def PackOps(data, packing_instructions, ops, huff):
  """ Packs (i.e. renders into wire-format) the operations in 'ops' into the
  BitBucket 'data', using the 'packing_instructions' and possibly the Huffman
  encoder 'huff'
  """
  seder = Spdy4SeDer()
  data.StoreBits(seder.SerializeInstructions(ops, packing_instructions,
                                             huff, 1234, True))

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
        self.WriteOpData(data, ops[orig_idx + i], huff)
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
      pack_fn(data, params, val, huff)

  def WriteControlFrameStreamId(self, data, stream_id):
    if (stream_id & 0x80000000):
      abort()
    data.StoreBits32(0x80000000 | stream_id)

  def WriteControlFrameBoilerplate(self,
      data,
      frame_len,
      flags,
      stream_id,
      frame_type):
    """ Writes the frame-length, flags, stream-id, and frame-type
    in SPDY4 format into the bit-bucket represented bt 'data'"""
    data.StoreBits16(frame_len)
    data.StoreBits8(flags)
    #data.StoreBits32(stream_id)
    self.WriteControlFrameStreamId(data, stream_id)
    data.StoreBits8(frame_type)

  def SerializeInstructions(self,
      ops,
      packing_instructions,
      huff,
      stream_id,
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
    self.WriteControlFrameBoilerplate(frame_bb, 0, 0, 0, 0)
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
                                        end_of_frame, stream_id, 0x8)
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
    return ops

class HeaderGroup(object):
  """ A HeaderGroup is a list of ValueEntries (VEs) which are the key-values to
  be instantiated as a header frame """
  def __init__(self):
    self.storage = dict()
    self.generation = 0

  def Empty(self):
    return not self.storage

  def IncrementGeneration(self):
    self.generation += 1

  def HasEntry(self, ve):
    retval = id(ve) in self.storage
    #if retval:
    #  print "Has Entry for %s: %s" % (ve['key'], ve['val'])
    #else:
    #  print " NO Entry for %s: %s" % (ve['key'], ve['val'])
    return retval

  def TouchEntry(self, ve):
    #print "TE:touched: %s: %s (%d)" % (ve['key'], ve['val'], self.generation)
    self.storage[id(ve)] = (ve, self.generation)

  def AddEntry(self, ve):
    if id(ve) in self.storage:
      raise StandardError()
    self.storage[id(ve)] = (ve, self.generation)
    #print "AE:  added: %s: %s (%d)", (ve['key'], ve['val'], self.generation)

  def RemoveEntry(self, ve):
    try:
      del self.storage[id(ve)]
    except KeyError:
      pass

  def FindOldEntries(self):
    def NotCurrent(x):
      return x != self.generation
    retval = [e for he,(e,g) in self.storage.iteritems() if NotCurrent(g)]
    return retval

  def GetEntries(self):
    return [e for he,(e, g) in self.storage.iteritems()]

  def Toggle(self, ve):
    try:
      #g = self.storage[id(ve)][1]
      del self.storage[id(ve)]
      #print "TG: removed: %s: %s (%d)" % (ve['key'], ve['val'], g)
    except KeyError:
      if id(ve) in self.storage:
        raise StandardError()
      self.storage[id(ve)] = (ve, self.generation)
      #print "TG:  added: %s: %s (%d)" % (ve['key'], ve['val'], self.generation)

class Storage(object):
  """ This object keeps track of key and LRU ids, all keys and values, and the
  mechanism for expiring key/value entries as necessary"""
  def __init__(self):  ####
    self.key_map = {}
    self.key_ids = IDStore()
    self.lru_ids = IDStore()
    self.state_size = 0
    self.num_vals = 0
    self.max_vals = 1024
    self.max_state_size = 64*1024
    self.pinned = None
    self.remove_val_cb = None
    self.lru = deque()
    self.lru_idx_to_ve = {}
    self.key_idx_to_ke = {}

  def PopOne(self):  ####
    """ Gets rid of the oldest entry on the LRU so long as
    we haven't yet hit the 'pin' (an entry which is None)
    TODO: This should skip entries in the header-group which is being
    processed, but since this is annoying to do in python, this function
    doesn't yet do it.
    """
    if not self.lru:
      return
    if self.lru[0] is None:
      # hit the pin.
      return
    ve = self.lru[0]
    if self.remove_val_cb:
      self.remove_val_cb(ve)
    self.RemoveVal(ve)

  def MakeSpace(self, space_required, adding_val):  ####
    """
    Makes enough space for 'space_required' new bytes and 'adding_val' new val
    entries by popping elements from the LRU (using PopOne)
    """
    while self.num_vals + adding_val > self.max_vals:
      if not self.PopOne():
        return
    while self.state_size + space_required > self.max_state_size:
      if not PopOne():
        return

  def FindKeyEntry(self, key): ####
    if key in self.key_map:
      return self.key_map[key]
    return None

  def FindKeyIdxByKey(self, key): ####
    ke = self.FindKeyEntry(key)
    if ke:
      return ke['key_idx']
    return -1

  def FindKeyByKeyIdx(self, key_idx):
    return self.key_idx_to_ke.get(key_idx, None)

  def IncrementRefCnt(self, ke): ####
    ke['ref_cnt'] += 1

  def DecrementRefCnt(self, ke): ####
    ke['ref_cnt'] -= 1

  def NewKE(self, key): ####
    return {'key_idx': self.key_ids.GetNext(),
            'ref_cnt': 0,
            'val_map': {},
            'key': key,
            }

  def NewVE(self, key, val, ke):  ####
    return {'lru_idx': None,
            'key': key,
            'val': val,
            'ke': ke,
            }

  def FindOrAddKey(self, key): ####
    ke = self.FindKeyEntry(key)
    if ke:
      return ke
    self.MakeSpace(len(key), 0)
    self.key_map[key] = ke = self.NewKE(key)
    key_idx = ke['key_idx']
    if key_idx in self.key_idx_to_ke:
      raise StandardError()
    self.key_idx_to_ke[key_idx] = ke
    self.state_size += len(key)
    return ke

  def InsertVal(self, key, val): ####
    ke = self.FindOrAddKey(key)
    if ke['val_map'].get(val, None) is not None:
      print "Hmm. This (%s) shouldn't have existed already" % val
      raise StandardError()
    self.IncrementRefCnt(ke)
    self.MakeSpace(len(val), 1)
    self.num_vals += 1
    ke['val_map'][val] = ve = self.NewVE(key, val, ke)
    self.DecrementRefCnt(ke)
    return ve

  def AddToHeadOfLRU(self, ve): ####
    if ve['lru_idx'] >= 0:
      raise StandardError()
    if ve is not None:
      lru_idx = self.lru_ids.GetNext()
      ve['lru_idx'] = lru_idx
      self.lru_idx_to_ve[lru_idx] = ve
      self.lru.append(ve)

  def GetVEFromLRUIdx(self, lru_idx):
    return self.lru_idx_to_ve.get(lru_idx, None)

  def MoveToHeadOfLRU(self, ve):  ####
    try:
      self.lru.remove(ve)
      self.lru.append(ve)
    except:
      pass

  def RemoveFromLRU(self, ve): ####
    # print "removing from LRU: (%r,%r, %d)" % (ve['key'], ve['val'], ve['lru_idx'])
    self.lru.remove(ve)
    lru_idx = ve['lru_idx']
    del self.lru_idx_to_ve[lru_idx]
    ve['lru_idx'] = None

  def RemoveFromValMap(self, ve): ####
    self.state_size -= len(ve['val'])
    self.num_vals -= 1
    del ve['ke']['val_map'][ve['val']]

  def MaybeRemoveFromKeyMap(self, ke): ####
    if not ke or len(ke['val_map']) > 0 or ke['ref_cnt'] > 0:
      return
    self.state_size -= len(ke['key'])

  def RemoveVal(self, ve): ####
    self.RemoveFromLRU(ve)
    self.RemoveFromValMap(ve)
    self.MaybeRemoveFromKeyMap(ve['ke'])

  def SetRemoveValCB(self, cb): ####
    self.remove_val_cb = cb

  def FindValEntry(self, ke, val): ####
    if ke is None:
      return None
    return ke['val_map'].get(val, None)

  def PinLRU(self):
    if self.pinned:
      raise StandardError()
    self.pinned = True
    self.lru.append(None)

  def UnPinLRU(self):
    if not self.pinned:
      raise StandardError()
    self.pinned = False
    self.lru = deque([x for x in self.lru if x is not None])


class Spdy4CoDe(object):
  def __init__(self):
    self.header_groups = {}
    self.huffman_table = None
    self.wf = WordFreak()
    self.storage = Storage()
    def RemoveVEFromAllHeaderGroups(ve):
      to_be_removed = []
      for group_id, header_group in self.header_groups.iteritems():
        #print "Removing %d from hg %d" % (ve['lru_idx'], group_id)
        header_group.RemoveEntry(ve)
        if header_group.Empty():
          to_be_removed.append(group_id)
      for group_id in to_be_removed:
        #print "Deleted group_id: %d" % group_id
        del header_group[group_id]

    self.storage.SetRemoveValCB(RemoveVEFromAllHeaderGroups)

    # TODO: Order this such that toggles for the initial request are all
    # together, and thus the client may use a single trang to get what it
    # wants.
    default_dict = {
        'date': '',
        ':scheme': 'https',
        ':method': 'get',
        ':path': '/',
        ':host': '',
        'cookie': '',
        ':status': '200',
        ':status-text': 'OK',
        ':version': '1.1',
        'accept': '',
        'accept-charset': '',
        'accept-encoding': '',
        'accept-language': '',
        'accept-ranges': '',
        'allow': '',
        'authorizations': '',
        'cache-control': '',
        'content-base': '',
        'content-encoding': '',
        'content-length': '',
        'content-location': '',
        'content-md5': '',
        'content-range': '',
        'content-type': '',
        'etag': '',
        'expect': '',
        'expires': '',
        'from': '',
        'if-match': '',
        'if-modified-since': '',
        'if-none-match': '',
        'if-range': '',
        'if-unmodified-since': '',
        'last-modified': '',
        'location': '',
        'max-forwards': '',
        'origin': '',
        'pragma': '',
        'proxy-authenticate': '',
        'proxy-authorization': '',
        'range': '',
        'referer': '',
        'retry-after': '',
        'server': '',
        'set-cookie': '',
        'status': '',
        'te': '',
        'trailer': '',
        'transfer-encoding': '',
        'upgrade': '',
        'user-agent': '',
        'user-agent': '',
        'vary': '',
        'via': '',
        'warning': '',
        'www-authenticate': '',
        'access-control-allow-origin': '',
        'content-disposition': '',
        'get-dictionary': '',
        'p3p': '',
        'x-content-type-options': '',
        'x-frame-options': '',
        'x-powered-by': '',
        'x-xss-protection': '',
        }
    for (k, v) in default_dict.iteritems():
      self.ExecuteOp(None, self.MakeKvsto(k, v))
      ke = self.storage.FindKeyEntry(k)
      ve = self.storage.FindValEntry(ke, v)
      ve['lru_idx'] = lru_idx = self.storage.lru_ids.GetNext()
      self.storage.lru_idx_to_ve[lru_idx] = ve

  def OpsToRealOps(self, in_ops):
    """ Packs in-memory format operations into wire format"""
    data = BitBucket()
    PackOps(data, packing_instructions, in_ops, self.huffman_table)
    return ListToStr(data.GetAllBits()[0])

  def RealOpsToOps(self, realops):
    """ Unpacks wire format operations into in-memory format"""
    bb = BitBucket()
    bb.StoreBits((StrToList(realops), len(realops)*8))
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

  def MakeClone(self, key_idx, val, use_huffman=False):
    return {'opcode': 'clone', 'val': val, 'key_idx': key_idx, 'huff': use_huffman}

  def MakeERef(self, key, value, use_huffman=False):
    return {'opcode': 'eref', 'key': key, 'val': value, 'huff': use_huffman}

  def FindOrMakeHeaderGroup(self, group_id):
    try:
      return self.header_groups[group_id]
    except KeyError:
      self.header_groups[group_id] = HeaderGroup()
      return self.header_groups[group_id]

  def TouchHeaderGroupEntry(self, group_id, ve):
    self.header_groups[group_id].TouchEntry(ve)

  def VEInHeaderGroup(self, group_id, ve):
    return self.header_groups[group_id].HasEntry(ve)

  def IdxToVE(self, idx):
    return self.storage.lru_idx_to_ve[idx]

  def DiscoverTurnOffs(self, group_id, instructions):
    """ Discovers the elements in the header-group which are not current, and
    thus should be removed from the header group (i.e. turned off)
    """
    toggles_off = []
    header_group = self.FindOrMakeHeaderGroup(group_id)
    for ve in header_group.FindOldEntries():
      toggles_off.append(self.MakeToggl(ve['lru_idx']))
    return toggles_off

  def RenumberVELruIdx(self, ve):
    lru_idx = ve['lru_idx']
    new_lru_idx = ve['lru_idx'] = self.storage.lru_ids.GetNext()
    del self.storage.lru_idx_to_ve[lru_idx]
    self.storage.lru_idx_to_ve[new_lru_idx] = ve

  def AdjustHeaderGroupEntries(self, group_id):
    """ Moves elements which have been referenced/modified to the head of the LRU
    and possibly renumbers them"""
    header_group = self.header_groups[group_id]
    for ve in sorted(header_group.GetEntries(),key=lambda x: x['lru_idx']):
      self.storage.MoveToHeadOfLRU(ve)
      self.RenumberVELruIdx(ve)

  def ExecuteInstructionsExceptERefs(self, group_id, instructions):
    if 'trang' in instructions:
      raise StandardError()
    for op in instructions['toggl']:
      self.ExecuteOp(group_id, op)
    for op in instructions['clone']:
      self.ExecuteOp(group_id, op)
    for op in instructions['kvsto']:
      self.ExecuteOp(group_id, op)

  def ProcessKV(self, key, val, group_id, instructions):
    """ Comes up with the appropriate operation for the key, value, and adds
    it into 'instructions'"""
    use_huffman = not key in bohe.ENCODERS
    ke = self.storage.FindKeyEntry(key)
    ve = self.storage.FindValEntry(ke, val)
    if ve is not None:
      if not self.VEInHeaderGroup(group_id, ve):
        instructions['toggl'].append(self.MakeToggl(ve['lru_idx']))
      else:
        self.TouchHeaderGroupEntry(group_id, ve)
    elif ke is not None:
      instructions['clone'].append(self.MakeClone(ke['key_idx'], val, use_huffman))
    else:
      instructions['kvsto'].append(self.MakeKvsto(key, val, use_huffman))

  def MakeOperations(self, headers, group_id):
    """ Computes the entire set of operations necessary to encode the 'headers'
    for header-group 'group_id'
    """
    instructions = {'toggl': [], 'clone': [], 'kvsto': [], 'eref': []}
    incremented_keys = []
    self.storage.PinLRU()
    self.FindOrMakeHeaderGroup(group_id)  # make the header group if necessary
    for k in headers.iterkeys():
      ke = self.storage.FindKeyEntry(k)
      if ke:
        self.storage.IncrementRefCnt(ke)
        incremented_keys.append(ke)
    for k,v in headers.iteritems():
      if k == 'cookie':
        splitvals = [x.lstrip(' ') for x in v.split(';')]
        splitvals.sort()
        for splitval in splitvals:
          self.ProcessKV(k, bohe.encode(k,splitval), group_id, instructions)
      else:
        self.ProcessKV(k, bohe.encode(k,v), group_id, instructions)

    turn_offs = self.DiscoverTurnOffs(group_id, instructions)
    instructions['toggl'].extend(turn_offs)
    self.ExecuteInstructionsExceptERefs(group_id, instructions)

    for ke in incremented_keys:
      self.storage.DecrementRefCnt(ke)
    # SerializeInstructions()
    self.storage.UnPinLRU()
    self.header_groups[group_id].IncrementGeneration()
    self.AdjustHeaderGroupEntries(group_id)
    #FormatOps(instructions, 'MO\t')
    return instructions

  def RealOpsToOpAndExecute(self, realops, group_id):
    """ Deserializes from SPDY4 wire format and executes the operations"""
    ops = self.RealOpsToOps(realops)
    #FormatOps(ops,'ROTOAE\t')
    self.storage.PinLRU()
    self.ExecuteOps(ops, group_id)
    self.storage.UnPinLRU()
    return ops

  def ExecuteOps(self, ops, group_id, ephemereal_headers=None):
    """ Executes a list of operations"""
    self.FindOrMakeHeaderGroup(group_id)  # make the header group if necessary
    if ephemereal_headers is None:
      ephemereal_headers = {}
    #print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
    for op in ops:
      self.ExecuteOp(group_id, op, ephemereal_headers)
    #print 'DONE'

  def ExecuteToggle(self, group_id, idx):
    self.header_groups[group_id].Toggle(self.IdxToVE(idx))

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
      key_idx = op['key_idx']
      # Clone - copies key and stores new value
      ke = self.storage.FindKeyByKeyIdx(key_idx)
      if ke is None:
        raise StandardError()
      ve = self.storage.InsertVal(ke['key'], op['val'])
      self.storage.AddToHeadOfLRU(ve)
      self.TouchHeaderGroupEntry(group_id, ve)
    elif opcode == 'kvsto':
      # kvsto - store key,value
      ve = self.storage.InsertVal(op['key'], op['val'])
      if group_id is not None:
        self.storage.AddToHeadOfLRU(ve)
        self.TouchHeaderGroupEntry(group_id, ve)
    elif opcode == 'eref' and ephemereal_headers is not None:
      ephemereal_headers[op['key']] = op['val']

  def GenerateAllHeaders(self, group_id):
    """ Given a group-id, generates the set of headers currently associated
    with that header group, and returns them.
    """
    headers = {}
    header_group = self.header_groups[group_id]

    for ve in sorted(header_group.GetEntries(),key=lambda x: x['lru_idx']):
      key = ve['key']
      val = ve['val']
      if key in headers:
        headers[key] = headers[key] + '\0' + val
      else:
        headers[key] = val
    if 'cookie' in headers:
      headers['cookie'] = headers['cookie'].replace('\0', '; ')
    self.AdjustHeaderGroupEntries(group_id)
    return headers


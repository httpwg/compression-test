# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import zlib
import re
import bohe
import struct
import header_freq_tables
import common_utils

from huffman import Huffman
from .. import BaseProcessor
from bit_bucket import BitBucket


# There are a number of TODOS in the spdy4
#      have near indices. Possibly renumber whever something is referenced)

class Processor(BaseProcessor):

  headers = []

  def __init__(self, options, is_request, params):
    BaseProcessor.__init__(self, options, is_request, params)
    if is_request:
      self.huff = huffman.Huffman(header_freq_tables.request_freq_table)
    else:
      self.huff = huffman.Huffman(header_freq_tables.response_freq_table)

  def compress(self, inp_headers, host):
    data = BitBucket()
    res = ''
    for k,v in inp_headers.items():
      if k in bohe.ID_TABLE:
        zz = data.NumBits()
        # encode as registered header
        data.StoreBits8(bohe.ID_TABLE.index(k) + 1)
        l = 0
        dohuff = True
        # Set the binary flag
        if k in bohe.ENCODERS:
          data.StoreBit(1)
          dohuff = False
        # Set the multiple values flag...
        if '\u00' in v:
          data.StoreBit(1)
        else:
          data.StoreBit(0)
        val = bohe.encode(k,v)
        if dohuff:
          val_as_list, len_in_bits = self.do_huff(self.huff, val)
        else:
          val_as_list = common_utils.StrToList(val)
          len_in_bits = len(val_as_list) *8
        data.StoreBits22(len(val_as_list))
        data.StoreBits( (val_as_list, len_in_bits) )
      else:
        data.StoreBits8(128 | len(k))
        data.StoreBits((common_utils.StrToList(k), len(k)*8))
        data.StoreBit(0) # assume not binary value for now
        if '\u00' in v:
          data.StoreBit(1)
        else:
          data.StoreBit(0)
        val_as_list, len_in_bits = self.do_huff(self.huff, v)
        data.StoreBits22(len(val_as_list))
        data.StoreBits((val_as_list, len_in_bits))
    return ''.join(common_utils.ListToStr(data.GetAllBits()[0]))

  def do_huff(self, huff, val):
    val_as_list = common_utils.StrToList(val)
    (val_as_list, len_in_bits) = huff.Encode(val_as_list, True)
    #len_in_bits = len(val_as_list) *8
    return val_as_list, len_in_bits
    

# NO DECOMPRESSION YET!
  # def decompress(self, compressed):
  #   header_group = 0
  #   out_real_ops = self.decompressor.Decompress(compressed)
  #   out_ops = self.decompressor.RealOpsToOpAndExecute(
  #       out_real_ops, header_group)
  #   return self.decompressor.GenerateAllHeaders(header_group)

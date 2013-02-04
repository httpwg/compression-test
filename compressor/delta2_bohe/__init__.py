# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import zlib
import re

import header_freq_tables
import spdy4_codec_impl
import huffman
import common_utils
from .. import BaseProcessor, strip_conn_headers

# There are a number of TODOS in the spdy4
#      have near indices. Possibly renumber whever something is referenced)

class Processor(BaseProcessor):
  """
  This class formats header frames in SPDY4 wire format, and then reads the
  resulting wire-formatted data and restores the data. Thus, it compresses and
  decompresses header data.

  It also keeps track of letter frequencies so that better frequency tables
  can eventually be constructed for use with the Huffman encoder.
  """
  def __init__(self, options, is_request, params):
    # 'params' is ignored
    self.compressor   = spdy4_codec_impl.Spdy4CoDe()
    self.decompressor = spdy4_codec_impl.Spdy4CoDe()
    self.options = options
    self.hosts = {}
    self.group_ids = common_utils.IDStore(2**31)
    self.wf = self.compressor.wf
    self.name = "delta2_bohe"
    if is_request:
      request_freq_table = header_freq_tables.request_freq_table
      self.compressor.huffman_table = huffman.Huffman(request_freq_table)
      self.decompressor.huffman_table = huffman.Huffman(request_freq_table)
    else:
      response_freq_table = header_freq_tables.response_freq_table
      self.compressor.huffman_table = huffman.Huffman(response_freq_table)
      self.decompressor.huffman_table = huffman.Huffman(response_freq_table)

  def PrintOps(self, ops):
    for op in ops:
      print "\t", spdy4_codec_impl.FormatOp(op)

  def compress(self, inp_headers, host):
    """
    'inp_headers' are the headers that will be processed
    'request_headers' are the request headers associated with this frame
       the host is extracted from this data. For a response, this would be
       the request that engendered the response. For a request, it is just
       the request again.

    It returns:
    (compressed_frame,
     wire_formatted_operations_before_compression,
     wire_formatted_operations_after_decompression,
     input_headers,
     outputted_headers_after_encode_decode,
     operations_as_computed_by_encoder,
     operations_as_recovered_after_decode)

    Note that compressing with an unmodified stream-compressor like gzip is
    effective, however it is insecure.
    """
    normalized_host = re.sub('[0-1a-zA-Z-\.]*\.([^.]*\.[^.]*)', '\\1',
                             host)
    if normalized_host in self.hosts:
      group_id = self.hosts[normalized_host]
    else:
      group_id = self.group_ids.GetNext()
      self.hosts[normalized_host] = group_id
    inp_ops = self.compressor.MakeOperations(strip_conn_headers(inp_headers), group_id)
    inp_real_ops = self.compressor.OpsToRealOps(inp_ops, group_id)
    compressed_blob = self.compressor.Compress(inp_real_ops)
    return compressed_blob

  # def decompress(self, compressed_blob):
  #   out_real_ops = self.decompressor.Decompress(compressed_blob)
  #   (group_id, out_ops) = self.decompressor.RealOpsToOpAndExecute(out_real_ops)
  #   out_headers = self.decompressor.GenerateAllHeaders(group_id)
  #   return out_headers

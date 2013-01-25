# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import zlib
from .. import BaseProcessor, spdy_dictionary, format_http1

class Processor(BaseProcessor):
  def __init__(self, options, is_request, params):
    BaseProcessor.__init__(self, options, is_request, params)
    self.compressor = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION,
                                       zlib.DEFLATED, 15, 8, zlib.Z_HUFFMAN_ONLY)
    self.compressor.compress(spdy_dictionary.spdy_dict);
    self.compressor.flush(zlib.Z_SYNC_FLUSH)

  def compress(self, in_headers, host):
    http1_msg = format_http1(in_headers)
    return ''.join([
                   self.compressor.compress(http1_msg),
                   self.compressor.flush(zlib.Z_SYNC_FLUSH)
                  ])
  
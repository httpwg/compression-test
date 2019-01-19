# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import zlib
import struct
from .. import spdy_dictionary, BaseProcessor

class Processor(BaseProcessor):
  def __init__(self, options, is_request, params):
    BaseProcessor.__init__(self, options, is_request, params)
    self.compressor = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION,
                                       zlib.DEFLATED, 15)
    if 'dict' in params:
      self.compressor.compress(spdy_dictionary.spdy_dict);
      self.compressor.flush(zlib.Z_SYNC_FLUSH)

  def compress(self, in_headers, host):
    raw_spdy3_frame = self.Spdy3HeadersFormat(in_headers)
    compress_me_payload = raw_spdy3_frame[12:]
    final_frame = raw_spdy3_frame[:12]
    final_frame += self.compressor.compress(compress_me_payload)
    final_frame += self.compressor.flush(zlib.Z_SYNC_FLUSH)
    return final_frame

  def Spdy3HeadersFormat(self, request):
    """
    Formats the provided headers in SPDY3 format, uncompressed
    """
    out_frame = []
    frame_len = 0
    for (key, val) in request.items():
      frame_len += 4
      frame_len += len(key)
      frame_len += 4
      frame_len += len(val)
    stream_id = 1
    num_kv_pairs = len(list(request.keys()))
#    out_frame.append(struct.pack('!L', 0x1 << 31 | 0x11 << 15 | 0x8))
#    out_frame.append(struct.pack('!L', frame_len))
#    out_frame.append(struct.pack('!L', stream_id))
#    out_frame.append(struct.pack('!L', num_kv_pairs))
    for (key, val) in request.items():
      out_frame.append(struct.pack('!L', len(key)))
      out_frame.append(key.encode('ascii'))
      out_frame.append(struct.pack('!L', len(val)))
      out_frame.append(val.encode('ascii'))
    return b''.join(out_frame)


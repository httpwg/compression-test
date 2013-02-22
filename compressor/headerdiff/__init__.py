# Copyright (c) 2012-2013, Canon Inc. 
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted only for the purpose of developing standards
# within the HTTPbis WG and for testing and promoting such standards within the
# IETF Standards Process. The following conditions are required to be met:
# - Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# - Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# - Neither the name of Canon Inc. nor the names of its contributors may be
#   used to endorse or promote products derived from this software without
#   specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY CANON INC. AND ITS CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL CANON INC. AND ITS CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import zlib

from headerDiffCodec import HeaderDiffCodec, IndexedHeader

from .. import BaseProcessor, strip_conn_headers, spdy_dictionary

#####################################################
## Class for representing a Header: (name, value)  ##
#####################################################
class HeaderTuple(object):
  def __init__(self, name, value):
    self.name = name
    self.value = value
    
  @classmethod
  def from_dict(cls, d):
    """Convert a dict of headers to a list of HeaderTuple."""
    return [HeaderTuple(k, v) for k, v in d.items()]
  
  @classmethod
  def split_from_dict(cls, d):
    """Convert a dict of headers to a list of HeaderTuple, splitting
    the cookies."""
    lst = []
    for k, v in d.items():
      if k == "cookie":
        lst.extend(HeaderTuple(k, vs.strip()) for vs in v.split(";"))
      else:
        lst.append(HeaderTuple(k, v))
    return lst
  
  def __str__(self):
    return self.name + ":" + self.value

  def __repr__(self):
    return self.name + ":" + self.value

BUFFER_SIZE = "buffer"
DEFLATE_SIZE = "deflate"

param_functions = {
  BUFFER_SIZE: int,
  DEFLATE_SIZE: int,
}

#####################################################
## Interface for the HeaderDiff codec              ##
#####################################################
class Processor(BaseProcessor):
  def __init__(self, options, is_request, params):
    BaseProcessor.__init__(self, options, is_request, params)
    
    param_dict = {
      BUFFER_SIZE: 32768,
      DEFLATE_SIZE: None,
    }
    for param in params:
      if "=" in param:
        name, value = param.split("=", 1)
      else:
        name = param
        value = None
      if name in param_functions:
        param_dict[name] = param_functions[name](value)
      else:
        param_dict[name] = value
    
    self.codec = HeaderDiffCodec(
      param_dict[BUFFER_SIZE],
      windowSize=param_dict[DEFLATE_SIZE],
      dict=spdy_dictionary.spdy_dict,
      )
  
  def compress(self, in_headers, host):
    hdrs = strip_conn_headers(in_headers)
    # Concat ":scheme", ":host" and ":path" into "url".
    if self.is_request:
      scheme = hdrs.get(":scheme", "http")
      del hdrs[":scheme"]
      host = hdrs.get(":host", "")
      del hdrs[":host"]
      path = hdrs.get(":path", "")
      del hdrs[":path"]
      hdrs["url"] = scheme + "://" + host + path
    
    hdrs = HeaderTuple.split_from_dict(hdrs)
    frame = self.codec.encodeHeaders(hdrs, self.is_request)
    return frame
  
  def decompress(self, compressed):
    hdrs = self.codec.decodeHeaders(compressed, self.is_request)
    hdrs = dict(hdrs)
    
    # Split "url".
    if self.is_request:
      url = hdrs.get("url")
      del hdrs["url"]
      scheme, hp = url.split(":", 1)
      host, path = hp[2:].split("/", 1)
      path = "/" + path
      hdrs[":scheme"] = scheme
      hdrs[":host"] = host
      hdrs[":path"] = path

    return hdrs

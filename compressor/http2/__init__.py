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

from .. import BaseProcessor

from http2Codec import HTTP2Codec

#===============================================================================
# Parameter definition
#===============================================================================
def parse_bool(value):
  if value is None:
    return True
  if value.lower() == "false":
    return False
  else:
    return True

IS_REQUEST = "is_request"
BUFFER_SIZE = "buffer_size"

param_functions = {
  BUFFER_SIZE: int,
}

#===============================================================================
# Processor class
#===============================================================================
def split_headers(d):
  lst = []
  for k, v in d.items():
    if k == "cookie":
      ch = ";"
    else:
      ch = "\0"
    hdrs = ((k, vs.strip()) for vs in v.split(ch))
    lst.extend(h for h in hdrs if h not in lst)
  return lst

def join_headers(lst):
  d = {}
  for k, v in lst:
    if k in d:
      if k == "cookie":
        d[k] += ";" + v
      else:
        d[k] += "\0" + v
    else:
      d[k] = v
  return d
      
class Processor(BaseProcessor):
  def __init__(self, options, is_request, params):
    BaseProcessor.__init__(self, options, is_request, params)
    
    param_dict = {
      IS_REQUEST: is_request,
      BUFFER_SIZE: 4096,
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
    
    codecClass = HTTP2Codec
    self.codec = codecClass(**param_dict)
  
  def compress(self, in_headers, host):
    headers = split_headers(in_headers)
    frame = self.codec.encode_headers(headers)
    
    return frame
  
  def decompress(self, compressed):
    headers = self.codec.decode_headers(compressed)
    return join_headers(headers)
    

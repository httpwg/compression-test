"""
Provides binary encoders for various http header value types
"""

from datetime import datetime
from Cookie import BaseCookie
from werkzeug import http
import sys
import struct
import md5
import re

class BaseEncoder(object):
  def __init__(self,is_request=True):
    self.NEW_EPOCH = self.epoch(datetime(self.sliding_epoch(),1,1,0,0,0,0))
    self.req = is_request
    
  def sliding_epoch(self):
    y = datetime.utcnow().year
    return y - (y % 21)
    
  def attempt_decode(self, value):
    if value is None:
      return value
    if re.match(r"^([a-fA-F0-9]{2})*$", value):
      return value.decode('hex_codec')
    elif re.match(r"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$", value): 
      return value.decode('base64_codec')
    else:
      return value

  # Encode a number as a uvarint (unsigned variable length integer)
  def enc_uvarint(self,val):
    if '' == val: 
      val = 0
    # on the offchance there are multiple values... TODO: handle this better...
    if hasattr(val,'split'): 
      vals = val.split('\x00')
    else:
      vals = [val]
    v = ''
    for val in vals:
      # TODO: Determine best encoding for multiple null separated values...
      val = max(0,int(val))  # TODO: should this be long?
      shift = True
      while shift:
        shift = val >> 7
        v += chr((val & 0x7F) | (0x80 if shift != 0 else 0x00))
        val = shift
    return v
    
  # Returns the given datetime as UNIX Epoch...
  def epoch(self,dt):
    return (dt - datetime.utcfromtimestamp(0)).total_seconds()

  def enc_date(self, val):
    try:
      return self.enc_uvarint(self.epoch(datetime.strptime(val, '%a, %d %b %Y %H:%M:%S GMT')) - self.NEW_EPOCH)
    except:
      # parse it as delta-seconds... at least try 
      try:
        val = max(0,int(val))
      except:
        # it's likely an invalid timestamp... just set to 0 and move on
        val = 0
      return self.enc_uvarint(val)

class UVarIntEncoder(BaseEncoder):
  
  def __init__(self,is_request=True):
    BaseEncoder.__init__(self,is_request)

  def encode(self, val):
    return self.enc_uvarint(val)

class DateEncoder(BaseEncoder):
    
  def __init__(self,is_request=True):
    BaseEncoder.__init__(self,is_request)

  # Optimized date encoding based on NEW_EPOCH value
  def encode(self, val):
    return self.enc_date(val)

class SetCookieEncoder(BaseEncoder):
    
  def __init__(self,is_request=True):
    BaseEncoder.__init__(self,is_request)
      
  # Encoding a Set-Cookie header value.. basic encoding (no extensions supported beyond HttpOnly and Secure)
  def encode(self, val):
    vals = val.split('\x00');
    encoded = ''
    for v in vals:
      if len(encoded) > 0:
        encoded += '\x00';
      v = v.replace(']','_') # work around parsing bug for some cookie values
      v = v.replace('[','_')
      cookie = BaseCookie(v)
      for n in cookie:
        morsel = cookie[n]
        encoded += '.' #TODO non-op... represent the bit flags.. add these in later
        encoded += self.enc_uvarint(len(n))
        encoded += n
        value = self.attempt_decode(morsel.value)
        encoded += self.enc_uvarint(len(value))
        encoded += value
        for f in ['path', 'domain']:
          l = len(morsel[f])
          encoded += struct.pack('!H',l)
          if l > 0:
            encoded += morsel[f]
        if len(morsel['max-age']) > 0:
          encoded += self.enc_uvarint(morsel['max-age'])
        else:
          encoded += self.enc_date(morsel['expires'])
    return encoded

class CookieEncoder(BaseEncoder):  
  def __init__(self,is_request=True):
    BaseEncoder.__init__(self,is_request)
    
  def encode(self, val):
    val = http.parse_dict_header(val)
    _v = ''
    for k,v in val.items():
      _v += '_' # simulate flags
      _v += self.enc_uvarint(len(k))
      _v += k
      value = self.attempt_decode(v)
      if not value is None:
        _v += self.enc_uvarint(len(value))
        _v += value
      else:
        _v += self.enc_uvarint(0)
    return _v

class CacheControlEncoder(BaseEncoder):
  def __init__(self,is_request=True):
    BaseEncoder.__init__(self,is_request)
    
  # Encoding Cache-Control...
  
  # adapted from httplib2 (https://code.google.com/p/httplib2/source/browse/python3/httplib2/__init__.py)# 
  # This is definitely not perfect as it does not properly handle commas within quoted strings
  # (e.g. multiple private and no-cache headers.. ignore this for now but TODO: need to fix)
  def _parse_cache_control(self, cc):
    cc = cc.replace('\x00', ',')
    retval = {}
    parts =  cc.split(',')
    parts_with_args = [tuple([x.strip().lower() for x in part.split("=", 1)]) for part in parts if -1 != part.find("=")]
    parts_wo_args = [(name.strip().lower(), 1) for name in parts if -1 == name.find("=")]
    retval = dict(parts_with_args + parts_wo_args)
    return retval
 
  def valOrZero(self, parts,m):
    if m in parts:
      return parts[m]
    else: 
      return 0
 
  def encode(self, val):
    parts = self._parse_cache_control(val)
    encoded = '_'; #represent first flags bit.. easier this way since we're just measuring space right now, TODO: Fix this
    encoded += self.enc_uvarint(self.valOrZero(parts,'max-age'))
    if self.req:
      encoded += self.enc_uvarint(self.valOrZero(parts,'max-stale'))
      encoded += self.enc_uvarint(self.valOrZero(parts,'min-fresh'))
      encoded += self.enc_uvarint(0) # num exts
    else:
      encoded += self.enc_uvarint(self.valOrZero(parts,'s-maxage'))
      for prt in ['no-cache','private']:
        if prt in parts and hasattr(parts[prt],'len') and len(parts[prt]) > 0:
          encoded += self.enc_uvarint(1)
          encoded += self.enc_uvarint(len(parts[prt]))
          encoded += parts[prt]
        else:
          encoded += self.enc_uvarint(0) 
      encoded += self.enc_uvarint(0) # num exts
    return encoded
    
class MethodEncoder(BaseEncoder):
  def __init__(self,is_request=True):
    BaseEncoder.__init__(self,is_request)

  def encode(self, val):
    methods = {
      'get': struct.pack('!B',1),
      'post': struct.pack('!B',2),
      'put': struct.pack('!B',3),
      'patch': struct.pack('!B',4),
      'delete': struct.pack('!B',5),
      'options': struct.pack('!B',6),
      'connect': struct.pack('!B',7),
    }
    if val in methods:
      return methods[val.lower()]
    else: 
      return val
 
class AcceptEncoder(BaseEncoder):
  def __init__(self,is_request=True):
    BaseEncoder.__init__(self,is_request)
    
  # Encode accept headers... this is LOSSY! Q-values are dropped,
  # values are sorted in order of preference. TODO: Investigate lossless alternatives
  def encode(self, val):
    vals = http.parse_accept_header(val)
    _v = ''
    for val in vals:
      if val[1] > 0.0:
        if len(_v) > 0:
          _v += '\x00'
        _v += val[0]
    return _v

class EtagEncoder(BaseEncoder):
  def __init__(self,is_request=True):
    BaseEncoder.__init__(self,is_request)
       
  # For experimentation, encodes etags as 16-byte md5 of the original etag.. in binary
  # lists of etags are encoded as [num_tags]*[[len][tag]]
  def encode(self, val):
    vals = val.split('\x00')
    _v = ''
    _v += self.enc_uvarint(len(vals))
    for val in vals:
      _v += struct.pack('!B',16)
      _v += md5.new(val).digest()
    return _v
   
class P3PEncoder(BaseEncoder): 
  p3p_table = [
    'NOI','ALL','CAO','IDC',
    'OTI','NON','DSP','COR',
    'MON','LAW','NID','CUR',
    'ADM','DEV','TAI','PSA',
    'PSD','IVA','IVD','CON',
    'HIS','TEL','OTP','OUR',
    'DEL','SAM','UNR','PUB',
    'OTR','NOR','STP','LEG',
    'BUS','IND','PHY','ONL',
    'UNI','PUR','FIN','COM',
    'NAV','INT','DEM','CNT',
    'STA','POL','HEA','PRE',
    'LOC','GOV','OTC','TST'
  ]
   
  def encode(self, val):
    val = http.parse_dict_header(val)
    _v = ''
    # policy refs
    if 'policyref' in val:
      _v += self.enc_uvarint(len(val['policyref']))
      _v += val['policyref']
    else:
      _v += self.enc_uvarint(0)
    cp = ''
    if 'CP' in val:
      tokens = val['CP'].split(' ')
      for token in tokens:
        # check for the fake P3P profiles like google produces... will ignore those nil values for now
        if not token[:3] in self.p3p_table:
          cp = '' 
          break
        q = (self.p3p_table.index(token[:3])+1) << 2
        if len(token) == 4:
          q |= ['a','i','o'].index(token[-1])
        cp += struct.pack('!B',q)
    if len(cp) > 0:
      _v += cp
    return _v

ENCODERS = {
  'last-modified': DateEncoder,
  'date': DateEncoder,
  'expires': DateEncoder,
  'if-modified-since': DateEncoder,
  'if-unmodified-since': DateEncoder,
  ':status': UVarIntEncoder,
  'content-length': UVarIntEncoder,
  'age': UVarIntEncoder,
  'set-cookie': SetCookieEncoder,
  'cookie': CookieEncoder,
  'cache-control': CacheControlEncoder,
  ':method': MethodEncoder,
  'accept': AcceptEncoder,
  'accept-language': AcceptEncoder,
  'accept-encoding': AcceptEncoder,
  'accept-charset': AcceptEncoder,
  'etag': EtagEncoder,
  'if-match': EtagEncoder,
  'if-none-match': EtagEncoder,
  'p3p': P3PEncoder
}

def encode(key,val,is_request=True):
  if key in ENCODERS:
    return ENCODERS[key](is_request).encode(val)
  else: 
    return val

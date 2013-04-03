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

"""
Codec implementing HeaderDiff format.
This implementation does not target efficiency but readability.
"""

from struct import pack, unpack
import zlib

from Huffman import request_codec, response_codec

# Different types of Delta-encoding
DELTA_FULL = "delta_full"   # Full Delta encoding
DELTA_BOUND = "delta_bound" # Delta encoding, with constraints on prefix end
DELTA_MAX = "delta_max"     # Delta encoding, with constraints on number of 
                            # references.

def common_prefix(s1, s2):
  l = min(len(s1), len(s2))
  for i in range(0, l):
    if s1[i] != s2[i]:
      return i
  return l

def common_prefix_limited(s1, s2, limits):
  l = common_prefix(s1, s2)
  for i in range(l, 0, -1):
    if s1[i-1] in limits:
#      print("  ({}) => {}:{} -> {}:{}".format(limits, l, s1[:l], i, s1[:i]))
      return i
#  print("  ({}) => {}:{} -> {}:{}".format(limits, l, s1[:l], 0, s1[:0]))
  return 0

class IndexedHeader(object):
  """
  Class used by Encoder for storing indexed headers
  (See Section 3.1.1 Header Table).
  """
  def __init__(self, name, value, index):
    self.name = name
    self.value = value
    self.index = index
    # Full is used by encoder as a key to find an indexed header
    self.full = name + value
    # Age is used by encoder when determining header representation
    self.age = 0
    # Number of usage as a reference for a delta-encoding
    self.delta_usage = 0

class HeaderRepresentation(object):
  """
  Class used by Encoder for defining a header representation
  (See Section 3.2 Header Representation).
  """
  def __init__(self):
    # Creates a default representation (i.e. literal without indexing)
    self.representation = LITERAL_REPRESENTATION
    self.referenceHeader = None
    self.indexing = NO_INDEXING
    self.commonPrefixLength = 0

class HeaderDiffCodec(object):
  """
  Codec implementing HeaderDiff format.
  """
  def __init__(self, maxIndexedSize,
      windowSize=None,
      dict=None,
      delta_usage=True,
      delta_type=(DELTA_BOUND, "/&= \coma"),
      huffman=False,
      **kwargs):
    # Maximum size of indexed headers
    # Size is measured as the sum of the header values indexed in the
    # header table (see Section 3.1.1 Header Table)
    self.indexedHeadersMaxSize = maxIndexedSize
    # Deflate parameters (optional)
    self.windowSize = windowSize
    self.dictionary = dict
    self.delta_usage = delta_usage
    self.delta_type, self.delta_param = delta_type
    if self.delta_type == DELTA_BOUND:
      self.delta_param = self.delta_param.replace("\\coma", ",")
    self.huffman = huffman
    if self.huffman:
      self.request_codec = request_codec
      self.response_codec = response_codec
      
    self.isRequest = kwargs["isRequest"]
#    print("Usage: {}, Type: {}, Param: '{}'".format(self.delta_usage,
#      self.delta_type, self.delta_param))
    # Initialize other variables
    self.initCodec()

  def initCodec(self):
    # If necessary, initialize compression and decompression contexts
    self.comp = None
    self.decomp = None
    if self.windowSize != None:
      self.comp = zlib.compressobj(
        zlib.Z_DEFAULT_COMPRESSION,
        zlib.DEFLATED,
        self.windowSize,
        8,
        zlib.Z_DEFAULT_STRATEGY)
      self.decomp = zlib.decompressobj()
      if self.dictionary:
        data = self.comp.compress(self.dictionary)
        data += self.comp.flush(zlib.Z_SYNC_FLUSH)
        self.decomp.decompress(data)
    # Encoder variables
    # Table comprising indexed headers
    self.headersTableEncoder = {}
    # Total length of indexed headers (see Section 3.1.1)
    self.headersTableEncoderSize = 0
    # List of header names (encoder, request) (see Section 3.1.2)
    self.headerNamesEncoderRequestTable = {}
    # List of header names (encoder, response) (see Section 3.1.2)
    self.headerNamesEncoderResponseTable = {}
    # Add pre-registered names to each table (see Appendix A)
    for i, name in enumerate(REGISTERED_HEADERS_REQUESTS):
      self.headerNamesEncoderRequestTable[name] = i
    for i, name in enumerate(REGISTERED_HEADERS_RESPONSES):
      self.headerNamesEncoderResponseTable[name] = i
    # Decoder variables
    # Decoded indexed headers
    self.indexedHeadersDecoder = []
    # Total length of indexed headers (see Section 3.1.1)
    self.indexedHeadersSizeDecoder = 0
    # List of header names (decoder, request) (see Section 3.1.2)
    self.headerNamesDecoderRequestTable = []
    # List of header names (decoder, response) (see Section 3.1.2)
    self.headerNamesDecoderResponseTable = []
    # Add pre-registered names to each table (see Appendix A)
    for name in REGISTERED_HEADERS_REQUESTS:
      self.headerNamesDecoderRequestTable.append(name)
    for name in REGISTERED_HEADERS_RESPONSES:
      self.headerNamesDecoderResponseTable.append(name)


  ######################
  ##   Decoder Part   ##
  ######################

  def decodeHeaders(self, stream, isRequest):
    """
    Method for decoding a set of headers.
    """
    self.decodedStream = stream[8:]
    self.decodedStreamIndex = 0
    # If Deflate was used, apply Inflate
    if self.windowSize != None:
      self.decodedStream = self.decomp.decompress(stream)
    # Initialize variables
    headers = [] # List of decoded headers
    # Decode number of headers
    nb = self.readNextByte()
    # Set the right table (see Section 3.1.2 Name Table)
    headerNamesTable = (self.headerNamesDecoderRequestTable if isRequest
                        else self.headerNamesDecoderResponseTable)
    # Decode headers
    while len(headers) < nb:
      #################################
      ## Check size of indexed data  ##
      #################################
      # Remark: this is not strictly necessary, but it allows
      # ensuring that encoder has the right behavior
      if self.indexedHeadersSizeDecoder > self.indexedHeadersMaxSize:
        raise Exception("Header table size exceeded (%i VS %i)" %
                        (self.indexedHeadersSizeDecoder,
                           self.indexedHeadersMaxSize))
      ###################################
      ## Start decoding of next header ##
      ###################################
      b0 = self.readNextByte()
      if (b0 & 0x80): # Check whether header is already indexed or not
        #####################################################
        ## Decoding of an already indexed header           ##
        ## (see Section 4.2 Indexed Header Representation) ##
        #####################################################
        index = b0 & 0x3f
        if (b0 & 0x40 != 0): # Check long index flag
          # Long index (see Section 4.2.2)
          index = self.readInteger(b0, 14) + 64
        # Add decoded header to the list
        headers.append(self.indexedHeadersDecoder[index])
      else:
        #####################################################
        ## Decoding of a header not already indexed        ##
        ## (see Sections 4.3 Literal Header Representation ##
        ## and 4.4 Delta Header Representation)            ##
        #####################################################
        # Initialize variables
        name = '' # Decoded header name
        value = '' # Decoder header value
        # Index of header used as a reference for delta encoding
        # and/or substitution indexing
        referenceIndex = 0
        # Remark: indexing flags are similar for
        # literal and delta representations
        incrementalIndexing = (b0 & 0x30) == 0x20
        substitutionIndexing = (b0 & 0x30) == 0x30
        indexFlag = incrementalIndexing or substitutionIndexing
        # Length of prefix bits (available for encoding an integer)
        #  - 5 bits if no indexing (see 4.3.1 and 4.4.1)
        #  - 4 bits if indexing  (see 4.3.2 and 4.4.2)
        prefixBits = 4 if indexFlag else 5
        if (b0 & 0x40): # Check whether header is encoded as a delta
          ##################################################
          ## Decoding of a delta encoded header           ##
          ## (see Section 4.4 Delta Header Representation)##
          ##################################################
          # Decode index of header referred to in this delta
          referenceIndex = self.readInteger(b0, prefixBits)
          # Name can now be determined based on referenceIndex
          name = self.indexedHeadersDecoder[referenceIndex][0]
          # Also decode common prefix length
          prefixLength = self.readInteger(b0, 0)
        # Below are cases different from delta encoding
        else:
          ####################################################
          ## Decoding of a literally encoded header         ##
          ## (see Section 4.3 Literal Header Representation)##
          ####################################################
          # Determine header name (index+1 is encoded in the stream)
          ref = self.readInteger(b0, prefixBits)
          if ref == 0:
            # Index 0 means new literal string
            name = self.readLiteralString()
            headerNamesTable.append(name)
          else:
            name = headerNamesTable[ref-1]
          # If substitution indexing, decode reference header index
          if substitutionIndexing:
            referenceIndex = self.readInteger(b0, 0)
        ##############################
        ## Decoding of header value ##
        ##############################
        value = self.readLiteralString()
        # If delta representation, apply delta to obtain full value
        if (b0 & 0x40) == 0x40:
          prefix = self.indexedHeadersDecoder[referenceIndex][1]
          value = prefix[:prefixLength]+ value
        # Add decoded headers
        headers.append((name, value))
        ######################################
        ## Apply indexing mode              ##
        ## (see section 3.1.1 Header Table) ##
        ######################################
        if substitutionIndexing:
          # Replace reference header
          reference = self.indexedHeadersDecoder[referenceIndex]
          self.indexedHeadersDecoder[referenceIndex] = (name, value)
          # Reference header value is accessible through reference[1]
          referenceValue = reference[1]
          self.indexedHeadersSizeDecoder+= (len(value)
                                            - len(referenceValue))
        elif incrementalIndexing:
          # Append to end as a new index
          self.indexedHeadersDecoder.append((name, value))
          self.indexedHeadersSizeDecoder+= len(value)

    # Return decoded headers
    return headers

  def readNextByte(self):
    """
    Method for reading the next byte.
    """
    (b,) = unpack("!B", self.decodedStream[self.decodedStreamIndex])
    self.decodedStreamIndex+= 1
    return b

  # Remark: this method does not aim at handling all possible cases,
  # but only the ones that may occur according to format specification.
  def readInteger(self, currentByte, prefixBits):
    """
    Method for decoding an integer value
    (see Section 4.1.1 Integer Representation).
    """
    # Read value encoded on prefix bits
    value = currentByte
    if prefixBits <= 8:
      value = value & MAX_VALUES[prefixBits]
    else:
      value = value & MAX_VALUES[prefixBits-8]
      value = (value << 8) | (self.readNextByte() & MAX_VALUES[8])
    if value == MAX_VALUES[prefixBits]:
      value = MAX_VALUES[prefixBits]
      # Read (value-(MAX_VALUES[prefixBits]+1)) on next bits
      b = self.readNextByte()
      f = 1
      while b & 0x80 > 0:
        value+= (b & 0x7f)*f
        f = f*128
        b = self.readNextByte()
      value+= b*f

    return value

  def readLiteralString(self):
    """
    Method for decoding a literal string value
    (see Section 4.1.2 String Literal Representation).
    """
    if self.huffman:
      if self.isRequest:
        value, length = self.request_codec.decode(self.decodedStream[self.decodedStreamIndex:])
      else:
        value, length = self.response_codec.decode(self.decodedStream[self.decodedStreamIndex:])
      self.decodedStreamIndex += length
    else:
      length = self.readInteger(0, 0) # No prefix bits
      value = self.decodedStream[self.decodedStreamIndex:
                                 self.decodedStreamIndex+length]
      self.decodedStreamIndex+= length
    return value

  ######################
  ##   Encoder Part   ##
  ######################

  def encodeHeaders(self, headerTuples, isRequest):
    """
    Method for encoding a set of headers
    """
    # Before encoding, increment age of indexed headers
    for ih in self.headersTableEncoder:
      self.headersTableEncoder[ih].age+= 1
    # Set the right table
    headerNamesTable = (self.headerNamesEncoderRequestTable if isRequest
                        else self.headerNamesEncoderResponseTable)

    # First, encode the number of headers (single byte)
    self.encodedStream = pack("!B", len(headerTuples))
    # Then, encode headers
    for he in headerTuples:
      headerName = he.name
      headerValue = he.value
      headerFull = headerName + headerValue
      # Determine representation
      hr = self.determineRepresentation(
        headerName,
        headerValue,
        isRequest)
      # Encode representation
      if hr.representation == INDEXED_REPRESENTATION:
        ############################
        ## Indexed representation ##
        ############################
        if hr.referenceHeader.index < 64:
          # Short index (see Section 4.2.1 Short Indexed Header)
          b = 0x80 | hr.referenceHeader.index
          self.encodedStream+= pack("!B", b)
        else:
          # Long index (see Section 4.2.2 Long Indexed Header)
          b = 0xc0
          self.writeInteger(b, 14, hr.referenceHeader.index-64)
      else:
        #############################################################
        ## Set indexing bits (same process for delta and literal)  ##
        ## (see Sections 4.3 Literal Header and 4.4 Delta Header)  ##
        #############################################################
        # First byte to be encoded (no flag if no indexing)
        b = 0x00
        # Length of prefix bits (available for encoding an integer)
        #  - 5 bits if no indexing (see 4.3.1 and 4.4.1)
        #  - 4 bits if indexing  (see 4.3.2 and 4.4.2)
        prefixBits = 4 if hr.indexing != NO_INDEXING else 5
        if hr.indexing == SUBSTITUTION_INDEXING:
          # Set substitution indexing flag
          b = 0x30
          # Remove replaced header, add new one and update table size
          # (as defined in Section 3.1.1 Header Table)
          del self.headersTableEncoder[hr.referenceHeader.full]
          self.headersTableEncoder[headerFull] = IndexedHeader(
            headerName,
            headerValue,
            hr.referenceHeader.index)
          self.headersTableEncoderSize-=len(hr.referenceHeader.value)
          self.headersTableEncoderSize+=len(headerValue)
        elif hr.indexing == INCREMENTAL_INDEXING:
          # Set incremental indexing flag
          b = 0x20
          # Add new header and update table size
          # (as defined in Section 3.1.1 Header Table)
          self.headersTableEncoder[headerFull] = IndexedHeader(
            headerName,
            headerValue,
            len(self.headersTableEncoder))
          self.headersTableEncoderSize+= len(headerValue)
        #############################################################
        ## Serialize using delta or literal representation         ##
        ## (see Sections 4.3 Literal Header and 4.4 Delta Header)  ##
        #############################################################
        if self.delta_usage and hr.representation == DELTA_REPRESENTATION:
          # Delta Representation (see Sections 4.4.1 and 4.4.2)
          # Set '01' at the beginning of the byte
          # (delta representation)
          b = b | 0x40
          # Encode reference header index
          self.writeInteger(b, prefixBits, hr.referenceHeader.index)
          # Encode common prefix length
          self.writeInteger(b, 0, hr.commonPrefixLength)
          hr.referenceHeader.delta_usage += 1
        else:
          # Literal Representation (see Sections 4.3.1 / 4.3.2)
          # '00' at the beginning of the byte (nothing to do)
          # Determine index of header name
          # (see Section 3.1.2 Name Table)
          nameIndex = (-1 if headerName not in headerNamesTable
                       else headerNamesTable[headerName])
          # Encode index + 1 (0 represents a new header name)
          self.writeInteger(b, prefixBits, nameIndex+1)
          # In case of new header name, encode name literally
          if nameIndex == -1:
            self.writeLiteralString(headerName)
            headerNamesTable[headerName] = len(headerNamesTable)
          # In case of substitution indexing,
          # encode index of reference header
          if hr.indexing == SUBSTITUTION_INDEXING:
            self.writeInteger(b, 0, hr.referenceHeader.index)
        # Encode value
        if self.delta_usage and hr.representation == DELTA_REPRESENTATION:
          valueToEncode = headerValue[hr.commonPrefixLength:]
        else:
          valueToEncode = headerValue
        self.writeLiteralString(valueToEncode)

    # Return encoded headers
    if self.windowSize != None:
      data = self.comp.compress(self.encodedStream)
      data += self.comp.flush(zlib.Z_SYNC_FLUSH)
    else:
      data = self.encodedStream
    
    # Generate Frame Header
    frame = pack("!HBBL", len(data), 0, 0, 0)
    return frame + data

  def determineRepresentation(self, headerName, headerValue, isRequest):
    """
    Method for determining header representation
    (encoder side only).
    """
    # Default encoding: literal without indexing
    hr = HeaderRepresentation()
    # Check possibility of indexed representation
    headerFull = headerName + headerValue
    if headerFull in self.headersTableEncoder:
      hr.representation = INDEXED_REPRESENTATION
      hr.referenceHeader = self.headersTableEncoder[headerFull]
      hr.referenceHeader.age = 0
      return hr

    if not self.delta_usage and headerName == ':path':
      return hr
    
    # Check possibility for delta representation
    deltaSubstitutionHeader = None
    # Length of common prefix in case of delta encoding
    commonPrefixLength = 0
    # Length added to indexed data in case of delta substitution indexing
    deltaSubstitutionAddedLength = 0
    
    if self.delta_usage:
      for hf in self.headersTableEncoder:
        indexedHeader = self.headersTableEncoder[hf]
        if indexedHeader.name == headerName:
          if self.delta_type == DELTA_MAX and indexedHeader.delta_usage >= self.delta_param:
            continue
          # Determine common prefix length between value to encode and
          # indexed header value
          iv = indexedHeader.value
          if self.delta_type == DELTA_FULL:
            k = common_prefix(headerValue, iv)
          elif self.delta_type == DELTA_BOUND:
            k = common_prefix_limited(headerValue, iv, self.delta_param)
          else:
            k = common_prefix(headerValue, iv)
          if k >= commonPrefixLength:
            commonPrefixLength = k
            deltaSubstitutionHeader = indexedHeader
            deltaSubstitutionAddedLength = (
              len(headerValue) - len(indexedHeader.value))

    lengthOK = (self.headersTableEncoderSize + len(headerValue) < self.indexedHeadersMaxSize)

    # Check whether replacing best match by this header in indexed
    # headers table would be ok
    deltaSubstitutionLengthOK = (
      self.headersTableEncoderSize + deltaSubstitutionAddedLength
      < self.indexedHeadersMaxSize)
    # Novelty is required for requests if header table size is "small"
    requireNovelty = isRequest and self.indexedHeadersMaxSize < 10000
    if commonPrefixLength > 1:
      # Use delta encoding
      hr.representation = DELTA_REPRESENTATION
      hr.referenceHeader = deltaSubstitutionHeader
      hr.commonPrefixLength = commonPrefixLength
      
      isNovel = deltaSubstitutionAddedLength > 15
      if not requireNovelty:
        isNovel = True
      if isNovel and lengthOK:
        hr.indexing = INCREMENTAL_INDEXING
      elif deltaSubstitutionLengthOK:
        hr.indexing = SUBSTITUTION_INDEXING
      return hr

    # If no delta encoding
    if lengthOK:
      hr.indexing = INCREMENTAL_INDEXING
      return hr

    # Look for least recently used indexed header
    # (it may be selected for literal substitution)
    lruh = None

    for hf in self.headersTableEncoder:
      indexedHeader = self.headersTableEncoder[hf]
      if indexedHeader.age > 1:
        addedDataLength = len(headerValue) - len(indexedHeader.value)
        remainingSize = self.indexedHeadersMaxSize - self.headersTableEncoderSize
        if addedDataLength < remainingSize:
          if not lruh:
            lruh = indexedHeader
          elif indexedHeader.age > lruh.age:
            lruh = indexedHeader

    if lruh != None:
        hr.indexing = SUBSTITUTION_INDEXING
        hr.referenceHeader = lruh

    return hr
  
  # Remark: This method does not aim at handling all possible cases,
  # but only the ones that may occur according to format specification.
  def writeInteger(self, currentByte, prefixBits, integerValue):
    """
    Method for encoding an integer value
    (see Section 4.1.1 Integer representation)
    """
    # First, check whether value can be encoded on prefix bits
    if integerValue < MAX_VALUES[prefixBits]:
      if prefixBits <= 8:
        currentByte = currentByte | integerValue
        self.encodedStream+= pack("!B", currentByte)
      else:
        b = currentByte | (integerValue >> 8)
        b = (b << 8) | (integerValue & 0xff)
        self.encodedStream+= pack("!H", b)
    # If value cannot be encoded on prefix bits, write it on next bytes
    else:
      # If prefix size is greater than 0,
      # write MAX_VALUE as the prefix
      if prefixBits > 0:
        currentByte = currentByte | MAX_VALUES[prefixBits]
        self.encodedStream+= pack("!B", currentByte)
      # Write value on next byte or bytes
      integerValue = integerValue - MAX_VALUES[prefixBits]
      if integerValue == 0:
        b = 0
        self.encodedStream+= pack("!B", b)
      while integerValue > 0:
        b = 0
        q = integerValue/128
        r = integerValue - q*128
        if q > 0:
          b = 0x80
        b = b | r
        self.encodedStream+= pack("!B", b)
        integerValue = q

  def writeLiteralString(self, value):
    """
    Method for literally encoding a string value
    (see Section 4.1.2 String Literal Representation)
    """
    if self.huffman:
      if self.isRequest:
        code = self.request_codec.encode(value)
      else:
        code = self.response_codec.encode(value)
      self.encodedStream += code
    else:
      self.writeInteger(0, 0, len(value))
      self.encodedStream+= str(value)


# Maximum values that can be encoded for prefixes of a given length
# (Section 4.1.1 Integer Representation)
MAX_VALUES = {0: 0x00, 4: 0x0f, 5: 0x1f, 6: 0x3f, 8: 0xff, 14: 0x3fff}
# Constants used for representation (Section 3.2 Header Representation)
LITERAL_REPRESENTATION = 0
INDEXED_REPRESENTATION = 1
DELTA_REPRESENTATION = 2
# Constants used for indexing
NO_INDEXING = 0
INCREMENTAL_INDEXING = 1
SUBSTITUTION_INDEXING = 2

# Pre-registered headers for requests (Appendix A.1)
REGISTERED_HEADERS_REQUESTS = [
    # Indexes 0 to 13 are always encoded on 1 byte
    'accept',
    'accept-charset',
    'accept-encoding',
    'accept-language',
    'cookie',
    ':method',
    'host',
    'if-modified-since',
    'keep-alive',
    ':host',
    ':scheme',
    ':path',
    'user-agent',
    ':version',
    'proxy-connection',
    'referer',
    # Next indexes are encoded on 1 or 2 byte(s)
    'accept-datetime',
    'authorization',
    'allow',
    'cache-control',
    'connection',
    'content-length',
    'content-md5',
    'content-type',
    'date',
    'expect',
    'from',
    'if-match',
    'if-none-match',
    'if-range',
    'if-unmodified-since',
    'max-forwards',
    'pragma',
    'proxy-authorization',
    'range',
    'te',
    'upgrade',
    'via',
    'warning',
    ]
# Pre-registered headers for responses (Appendix A.2)
REGISTERED_HEADERS_RESPONSES = [
    # Indexes 0 to 13 are always encoded on 1 byte
    'age',
    'cache-control',
    'content-length',
    'content-type',
    'date',
    'etag',
    'expires',
    'last-modified',
    'server',
    'set-cookie',
    ':status',
    'vary',
    ':version',
    'via',
    # Next indexes are encoded on 1 or 2 byte(s)
    ':status-text',
    'access-control-allow-origin',
    'accept-ranges',
    'allow',
    'connection',
    'content-disposition',
    'content-encoding',
    'content-language',
    'content-location',
    'content-md5',
    'content-range',
    'link',
    'location',
    'p3p',
    'pragma',
    'proxy-authenticate',
    'refresh',
    'retry-after',
    'strict-transport-security',
    'trailer',
    'transfer-encoding',
    'warning',
    'www-authenticate',
    ]

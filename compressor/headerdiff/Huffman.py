# -*- coding: utf-8 -*-
#
# $Id: binary4_codec.py 22698 2012-12-07 14:59:34Z ruellan $
# $HeadURL: https://svn-td3/repository/Projects/Wide/SPDY/trunk/header/src/binary4_codec.py $
# $LastChangedDate: 2012-12-07 15:59:34 +0100 (ven., 07 d�c. 2012) $
# $LastChangedRevision: 22698 $
# $LastChangedBy: ruellan $
#
# Copyright (c) 2012-2013, Canon Research Centre France SAS.
# Confidential. All rights reserved.
#
# Author:
#  ruellan
# Description:
#  Static Huffman encoder/decoder

#===============================================================================
# Tree building
#===============================================================================
class Node(object):
  """Class representing a Node in the Huffman tree."""
  def __init__(self, priority, symbol=None,
      left_child=None, right_child=None):
    self.priority = priority
    self.symbol = symbol
    self.left_child = left_child
    self.right_child = right_child
    self.parent = None
  
  def string_encoding(self):
    if self.parent:
      if self.parent.left_child == self:
        code = "0"
      else:
        code = "1"
      return self.parent.string_encoding() + code
    else:
      return ""
  
  def encoding(self):
    if self.parent:
      v, l = self.parent.encoding()
      if self.parent.left_child == self:
        return (v << 1), l + 1
      else:
        return (v << 1) + 1, l + 1
    else:
      return 0, 0
  
  def decode(self, code):
    if not self.left_child:
      return self.symbol, code
    else:
      if code[0] == "0":
        return self.left_child.decode(code[1:])
      else:
        return self.right_child.decode(code[1:])
  
  def __add__(self, other):
    res = Node(self.priority + other.priority,
      symbol="",
      left_child=self, right_child=other)
    self.parent = res
    other.parent = res
    return res
  
  def prt(self):
    l = ["{:6s} -- {:15s} -> {}".format(self.encoding(), self.symbol, self.priority)]
    if self.left_child:
      l.extend("0- " + s for s in self.left_child.prt())
      l.extend("1- " + s for s in self.right_child.prt())
    return l
  
  def __str__(self):
    return "{}:{}".format(self.symbol, self.priority)
  
def pick_node(l1, l2):
  if not l1:
    return l2.pop(0)
  if not l2:
    return l1.pop(0)
  if l1[0].priority <= l2[0].priority:
    return l1.pop(0)
  else:
    return l2.pop(0)
  
def create_tree(symbols):
  original_nodes = [Node(v, symbol=k) for k, v in symbols.items()]
  
  onodes = sorted(original_nodes, key=lambda n: n.priority)
  nnodes = []
  
  while len(onodes) + len(nnodes) >= 2:
    n1 = pick_node(onodes, nnodes)
    n2 = pick_node(onodes, nnodes)
    nnodes.append(n1 + n2)

  return original_nodes, nnodes[0]

#===============================================================================
# Encoding/Decoding
#===============================================================================
def normalize_stats(stats):
  """Normalize frequency statistics."""
  return dict((chr(k) if k < 256 else k, v if v else 1) for k, v in stats.items())

class BitEncoder(object):
  """Class for writing group of bits to a string."""
  def __init__(self):
    self.reset()
  
  def reset(self):
    self.bytes = ""
    self.current = 0x00
    self.free = 8
    
  def push_bits(self, value, count):
    while count:
      if self.free <= count:
        c = (self.current << self.free) + ((value >> (count - self.free)) & (0xFF >> (8 - self.free)))
        self.bytes += chr(c)
        count -= self.free
        self.current = 0x00
        self.free = 8
      else:
        self.current = (self.current << count) + (value & (0xFF >> (8 - count)))
        self.free -= count
        count = 0
  
  def code(self):
    if self.free < 8:
      c = self.current << self.free
      self.bytes += chr(c)
    return self.bytes

class BitDecoder(object):
  """Class for reading bits one by one from a string."""
  masks = [
    0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01
    ]
  def __init__(self, code=None):
    self.reset(code)
  
  def reset(self, code):
    self.code = code
    self.index = 0
    self.current = 0
    self.bit = 8
  
  def next_bit(self):
    if self.bit >= 8:
      self.current = ord(self.code[self.index])
      self.index += 1
      self.bit = 0
    
    bit = self.current & self.masks[self.bit]
    self.bit += 1
    return bit
  
  def has_bits(self):
    return self.index < len(self.code) or self.bit < 8
    
class HuffmanCodec(object):
  """Class for encoding/decoding strings."""
  def __init__(self, stats):
    stats = normalize_stats(stats)
    nodes, root = create_tree(stats)
    self.encoder = dict((n.symbol, n.encoding()) for n in nodes)
    self.bit_encoder = BitEncoder()
    self.root = root
    self.bit_decoder = BitDecoder()
  
  def encode(self, s):
    self.bit_encoder.reset()
    for c in s:
      code = self.encoder[c]
      self.bit_encoder.push_bits(*code)
    self.bit_encoder.push_bits(*self.encoder[256])
    return self.bit_encoder.code()
  
  def decode(self, s):
    last = 0
    res = ""
    self.bit_decoder.reset(s)
    while last != 256:
      node = self.root
      while node.left_child:
        code = self.bit_decoder.next_bit()
        if code:
          node = node.right_child
        else:
          node = node.left_child
      last = node.symbol
      if type(last) != int:
        res += last
    
    return res, self.bit_decoder.index

#===============================================================================
# Request stats
#===============================================================================
request_stats = {
  0x00:      0, # ''
  0x01:      0, # ''
  0x02:      0, # ''
  0x03:      0, # ''
  0x04:      0, # ''
  0x05:      0, # ''
  0x06:      0, # ''
  0x07:      0, # ''
  0x08:      0, # ''
  0x09:      0, # ''
  0x0a:      0, # ''
  0x0b:      0, # ''
  0x0c:      0, # ''
  0x0d:      0, # ''
  0x0e:      0, # ''
  0x0f:      0, # ''
  0x10:      0, # ''
  0x11:      0, # ''
  0x12:      0, # ''
  0x13:      0, # ''
  0x14:      0, # ''
  0x15:      0, # ''
  0x16:      0, # ''
  0x17:      0, # ''
  0x18:      0, # ''
  0x19:      0, # ''
  0x1a:      0, # ''
  0x1b:      0, # ''
  0x1c:      0, # ''
  0x1d:      0, # ''
  0x1e:      0, # ''
  0x1f:      0, # ''
  0x20:   1026, # ' '
  0x21:    944, # '!'
  0x22:    150, # '"'
  0x23:    155, # '#'
  0x24:    114, # '$'
  0x25:  43769, # '%'
  0x26:  24855, # '&'
  0x27:    113, # '''
  0x28:    968, # '('
  0x29:   1049, # ')'
  0x2a:    889, # '*'
  0x2b:   1089, # '+'
  0x2c:   4008, # ','
  0x2d:  31547, # '-'
  0x2e:  46976, # '.'
  0x2f:  30217, # '/'
  0x30:  61671, # '0'
  0x31:  64539, # '1'
  0x32:  73324, # '2'
  0x33:  47629, # '3'
  0x34:  32652, # '4'
  0x35:  34202, # '5'
  0x36:  29060, # '6'
  0x37:  33486, # '7'
  0x38:  28244, # '8'
  0x39:  31614, # '9'
  0x3a:   2466, # ':'
  0x3b:   4941, # ';'
  0x3c:     18, # '<'
  0x3d:  36853, # '='
  0x3e:     63, # '>'
  0x3f:   3891, # '?'
  0x40:    152, # '@'
  0x41:  15737, # 'A'
  0x42:   8813, # 'B'
  0x43:  10216, # 'C'
  0x44:  11895, # 'D'
  0x45:   6637, # 'E'
  0x46:  18246, # 'F'
  0x47:   3816, # 'G'
  0x48:   4529, # 'H'
  0x49:   5458, # 'I'
  0x4a:   3659, # 'J'
  0x4b:   2504, # 'K'
  0x4c:   4699, # 'L'
  0x4d:   5945, # 'M'
  0x4e:   4391, # 'N'
  0x4f:   4581, # 'O'
  0x50:   4264, # 'P'
  0x51:   4223, # 'Q'
  0x52:   4877, # 'R'
  0x53:   5744, # 'S'
  0x54:   7163, # 'T'
  0x55:   4396, # 'U'
  0x56:   4407, # 'V'
  0x57:   4514, # 'W'
  0x58:   5509, # 'X'
  0x59:   4247, # 'Y'
  0x5a:   2883, # 'Z'
  0x5b:    257, # '['
  0x5c:      0, # '\'
  0x5d:    274, # ']'
  0x5e:    142, # '^'
  0x5f:  26219, # '_'
  0x60:     17, # '`'
  0x61:  51091, # 'a'
  0x62:  21671, # 'b'
  0x63:  45189, # 'c'
  0x64:  34389, # 'd'
  0x65:  76843, # 'e'
  0x66:  23063, # 'f'
  0x67:  31026, # 'g'
  0x68:  19036, # 'h'
  0x69:  51279, # 'i'
  0x6a:  14245, # 'j'
  0x6b:  11033, # 'k'
  0x6c:  34184, # 'l'
  0x6d:  30439, # 'm'
  0x6e:  42519, # 'n'
  0x6f:  44796, # 'o'
  0x70:  36591, # 'p'
  0x71:   5376, # 'q'
  0x72:  40241, # 'r'
  0x73:  48979, # 's'
  0x74:  56413, # 't'
  0x75:  26014, # 'u'
  0x76:  11371, # 'v'
  0x77:  18784, # 'w'
  0x78:  10070, # 'x'
  0x79:   9174, # 'y'
  0x7a:   5963, # 'z'
  0x7b:     29, # '{'
  0x7c:   1531, # '|'
  0x7d:     29, # '}'
  0x7e:    490, # '~'
  0x7f:      0, # ''
  0x80:      0, # ''
  0x81:      0, # ''
  0x82:      0, # ''
  0x83:      0, # ''
  0x84:      0, # ''
  0x85:      0, # ''
  0x86:      0, # ''
  0x87:      0, # ''
  0x88:      0, # ''
  0x89:      0, # ''
  0x8a:      0, # ''
  0x8b:      0, # ''
  0x8c:      0, # ''
  0x8d:      0, # ''
  0x8e:      0, # ''
  0x8f:      0, # ''
  0x90:      0, # ''
  0x91:      0, # ''
  0x92:      0, # ''
  0x93:      0, # ''
  0x94:      0, # ''
  0x95:      0, # ''
  0x96:      0, # ''
  0x97:      0, # ''
  0x98:      0, # ''
  0x99:      0, # ''
  0x9a:      0, # ''
  0x9b:      0, # ''
  0x9c:      0, # ''
  0x9d:      0, # ''
  0x9e:      0, # ''
  0x9f:      0, # ''
  0xa0:      0, # ''
  0xa1:      0, # ''
  0xa2:      0, # ''
  0xa3:      0, # ''
  0xa4:      0, # ''
  0xa5:      0, # ''
  0xa6:      0, # ''
  0xa7:      0, # ''
  0xa8:      0, # ''
  0xa9:      0, # ''
  0xaa:      0, # ''
  0xab:      0, # ''
  0xac:      0, # ''
  0xad:      0, # ''
  0xae:      0, # ''
  0xaf:      0, # ''
  0xb0:      0, # ''
  0xb1:      0, # ''
  0xb2:      0, # ''
  0xb3:      0, # ''
  0xb4:      0, # ''
  0xb5:      0, # ''
  0xb6:      0, # ''
  0xb7:      0, # ''
  0xb8:      0, # ''
  0xb9:      0, # ''
  0xba:      0, # ''
  0xbb:      0, # ''
  0xbc:      0, # ''
  0xbd:      0, # ''
  0xbe:      0, # ''
  0xbf:      0, # ''
  0xc0:      0, # ''
  0xc1:      0, # ''
  0xc2:      0, # ''
  0xc3:      0, # ''
  0xc4:      0, # ''
  0xc5:      0, # ''
  0xc6:      0, # ''
  0xc7:      0, # ''
  0xc8:      0, # ''
  0xc9:      0, # ''
  0xca:      0, # ''
  0xcb:      0, # ''
  0xcc:      0, # ''
  0xcd:      0, # ''
  0xce:      0, # ''
  0xcf:      0, # ''
  0xd0:      0, # ''
  0xd1:      0, # ''
  0xd2:      0, # ''
  0xd3:      0, # ''
  0xd4:      0, # ''
  0xd5:      0, # ''
  0xd6:      0, # ''
  0xd7:      0, # ''
  0xd8:      0, # ''
  0xd9:      0, # ''
  0xda:      0, # ''
  0xdb:      0, # ''
  0xdc:      0, # ''
  0xdd:      0, # ''
  0xde:      0, # ''
  0xdf:      0, # ''
  0xe0:      0, # ''
  0xe1:      0, # ''
  0xe2:      0, # ''
  0xe3:      0, # ''
  0xe4:      0, # ''
  0xe5:      0, # ''
  0xe6:      0, # ''
  0xe7:      0, # ''
  0xe8:      0, # ''
  0xe9:      0, # ''
  0xea:      0, # ''
  0xeb:      0, # ''
  0xec:      0, # ''
  0xed:      0, # ''
  0xee:      0, # ''
  0xef:      0, # ''
  0xf0:      0, # ''
  0xf1:      0, # ''
  0xf2:      0, # ''
  0xf3:      0, # ''
  0xf4:      0, # ''
  0xf5:      0, # ''
  0xf6:      0, # ''
  0xf7:      0, # ''
  0xf8:      0, # ''
  0xf9:      0, # ''
  0xfa:      0, # ''
  0xfb:      0, # ''
  0xfc:      0, # ''
  0xfd:      0, # ''
  0xfe:      0, # ''
  0xff:      0, # ''
  0x100:  22803, # ''
}

#===============================================================================
# Response stats
#===============================================================================
response_stats = {
  0x00:      0, # ''
  0x01:      0, # ''
  0x02:      0, # ''
  0x03:      0, # ''
  0x04:      0, # ''
  0x05:      0, # ''
  0x06:      0, # ''
  0x07:      0, # ''
  0x08:      0, # ''
  0x09:      0, # ''
  0x0a:      0, # ''
  0x0b:      0, # ''
  0x0c:      0, # ''
  0x0d:      0, # ''
  0x0e:      0, # ''
  0x0f:      0, # ''
  0x10:      0, # ''
  0x11:      0, # ''
  0x12:      0, # ''
  0x13:      0, # ''
  0x14:      0, # ''
  0x15:      0, # ''
  0x16:      0, # ''
  0x17:      0, # ''
  0x18:      0, # ''
  0x19:      0, # ''
  0x1a:      0, # ''
  0x1b:      0, # ''
  0x1c:      0, # ''
  0x1d:      0, # ''
  0x1e:      0, # ''
  0x1f:      0, # ''
  0x20:  57434, # ' '
  0x21:    468, # '!'
  0x22:   6017, # '"'
  0x23:    156, # '#'
  0x24:     61, # '$'
  0x25:   2379, # '%'
  0x26:   1535, # '&'
  0x27:    188, # '''
  0x28:   1354, # '('
  0x29:   1854, # ')'
  0x2a:    408, # '*'
  0x2b:   1088, # '+'
  0x2c:   4088, # ','
  0x2d:  12270, # '-'
  0x2e:  12094, # '.'
  0x2f:   5389, # '/'
  0x30:  51167, # '0'
  0x31:  49470, # '1'
  0x32:  46318, # '2'
  0x33:  34850, # '3'
  0x34:  32732, # '4'
  0x35:  29867, # '5'
  0x36:  23980, # '6'
  0x37:  24184, # '7'
  0x38:  25422, # '8'
  0x39:  24720, # '9'
  0x3a:  28394, # ':'
  0x3b:   3104, # ';'
  0x3c:     19, # '<'
  0x3d:   8304, # '='
  0x3e:     90, # '>'
  0x3f:    216, # '?'
  0x40:     15, # '@'
  0x41:   7970, # 'A'
  0x42:   3660, # 'B'
  0x43:   5013, # 'C'
  0x44:   6058, # 'D'
  0x45:   4429, # 'E'
  0x46:   5438, # 'F'
  0x47:  22479, # 'G'
  0x48:   2356, # 'H'
  0x49:   4079, # 'I'
  0x4a:   3624, # 'J'
  0x4b:   1719, # 'K'
  0x4c:   2720, # 'L'
  0x4d:  24732, # 'M'
  0x4e:   4641, # 'N'
  0x4f:   4512, # 'O'
  0x50:   4081, # 'P'
  0x51:   2166, # 'Q'
  0x52:   3377, # 'R'
  0x53:   6182, # 'S'
  0x54:  25239, # 'T'
  0x55:   3518, # 'U'
  0x56:   2892, # 'V'
  0x57:   2336, # 'W'
  0x58:   2080, # 'X'
  0x59:   2080, # 'Y'
  0x5a:   1882, # 'Z'
  0x5b:    368, # '['
  0x5c:     96, # '\'
  0x5d:    436, # ']'
  0x5e:     43, # '^'
  0x5f:   3289, # '_'
  0x60:     11, # '`'
  0x61:  21432, # 'a'
  0x62:   9701, # 'b'
  0x63:  20280, # 'c'
  0x64:  13496, # 'd'
  0x65:  21771, # 'e'
  0x66:  11557, # 'f'
  0x67:   6700, # 'g'
  0x68:   6961, # 'h'
  0x69:  11591, # 'i'
  0x6a:   3168, # 'j'
  0x6b:   3305, # 'k'
  0x6c:   7927, # 'l'
  0x6d:   8196, # 'm'
  0x6e:  10878, # 'n'
  0x6f:  14524, # 'o'
  0x70:  10058, # 'p'
  0x71:   2567, # 'q'
  0x72:  11052, # 'r'
  0x73:   9721, # 's'
  0x74:  12552, # 't'
  0x75:   7250, # 'u'
  0x76:   4429, # 'v'
  0x77:   3763, # 'w'
  0x78:   5260, # 'x'
  0x79:   4208, # 'y'
  0x7a:   2565, # 'z'
  0x7b:      7, # '{'
  0x7c:     58, # '|'
  0x7d:     15, # '}'
  0x7e:     19, # '~'
  0x7f:      0, # ''
  0x80:      0, # ''
  0x81:      0, # ''
  0x82:      0, # ''
  0x83:      0, # ''
  0x84:      0, # ''
  0x85:      0, # ''
  0x86:      0, # ''
  0x87:      0, # ''
  0x88:      0, # ''
  0x89:      0, # ''
  0x8a:      0, # ''
  0x8b:      0, # ''
  0x8c:      0, # ''
  0x8d:      0, # ''
  0x8e:      0, # ''
  0x8f:      0, # ''
  0x90:      0, # ''
  0x91:      0, # ''
  0x92:      0, # ''
  0x93:      0, # ''
  0x94:      0, # ''
  0x95:      0, # ''
  0x96:      0, # ''
  0x97:      0, # ''
  0x98:      0, # ''
  0x99:      0, # ''
  0x9a:      0, # ''
  0x9b:      0, # ''
  0x9c:      0, # ''
  0x9d:      0, # ''
  0x9e:      0, # ''
  0x9f:      0, # ''
  0xa0:      0, # ''
  0xa1:      0, # ''
  0xa2:      0, # ''
  0xa3:      0, # ''
  0xa4:      0, # ''
  0xa5:      0, # ''
  0xa6:      0, # ''
  0xa7:      0, # ''
  0xa8:      0, # ''
  0xa9:      0, # ''
  0xaa:      0, # ''
  0xab:      0, # ''
  0xac:      0, # ''
  0xad:      0, # ''
  0xae:      0, # ''
  0xaf:      0, # ''
  0xb0:      0, # ''
  0xb1:      0, # ''
  0xb2:      0, # ''
  0xb3:      0, # ''
  0xb4:      0, # ''
  0xb5:      0, # ''
  0xb6:      0, # ''
  0xb7:      0, # ''
  0xb8:      0, # ''
  0xb9:      0, # ''
  0xba:      0, # ''
  0xbb:      0, # ''
  0xbc:      0, # ''
  0xbd:      0, # ''
  0xbe:      0, # ''
  0xbf:      0, # ''
  0xc0:      0, # ''
  0xc1:      0, # ''
  0xc2:      0, # ''
  0xc3:      0, # ''
  0xc4:      0, # ''
  0xc5:      0, # ''
  0xc6:      0, # ''
  0xc7:      0, # ''
  0xc8:      0, # ''
  0xc9:      0, # ''
  0xca:      0, # ''
  0xcb:      0, # ''
  0xcc:      0, # ''
  0xcd:      0, # ''
  0xce:      0, # ''
  0xcf:      0, # ''
  0xd0:      0, # ''
  0xd1:      0, # ''
  0xd2:      0, # ''
  0xd3:      0, # ''
  0xd4:      0, # ''
  0xd5:      0, # ''
  0xd6:      0, # ''
  0xd7:      0, # ''
  0xd8:      0, # ''
  0xd9:      0, # ''
  0xda:      0, # ''
  0xdb:      0, # ''
  0xdc:      0, # ''
  0xdd:      0, # ''
  0xde:      0, # ''
  0xdf:      0, # ''
  0xe0:      0, # ''
  0xe1:      0, # ''
  0xe2:      0, # ''
  0xe3:      0, # ''
  0xe4:      0, # ''
  0xe5:      0, # ''
  0xe6:      0, # ''
  0xe7:      0, # ''
  0xe8:      0, # ''
  0xe9:      0, # ''
  0xea:      0, # ''
  0xeb:      0, # ''
  0xec:      0, # ''
  0xed:      0, # ''
  0xee:      0, # ''
  0xef:      0, # ''
  0xf0:      0, # ''
  0xf1:      0, # ''
  0xf2:      0, # ''
  0xf3:      0, # ''
  0xf4:      0, # ''
  0xf5:      0, # ''
  0xf6:      0, # ''
  0xf7:      0, # ''
  0xf8:      0, # ''
  0xf9:      0, # ''
  0xfa:      0, # ''
  0xfb:      0, # ''
  0xfc:      0, # ''
  0xfd:      0, # ''
  0xfe:      0, # ''
  0xff:      0, # ''
  0x100:  57125, # ''
}

request_codec = HuffmanCodec(request_stats)
response_codec = HuffmanCodec(response_stats)

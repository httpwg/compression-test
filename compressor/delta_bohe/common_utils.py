# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.



def ListToStr(val):
  """ Takes a list of ints and makes it into a string """
  return ''.join(['%c' % c for c in val])

def StrToList(val):
  """ Takes a string and makes it into a list of ints (<= 8 bits each)"""
  return [ord(c) for c in val]


def MakeReadableString(val):
  """ Takes a string and returns a normalized version which allows
  interpretation of nonprinting characters, but easier to read than just
  hex."""
  printable = string.digits + string.letters + string.punctuation + ' ' + '\t'
  out = []
  for c in val:
    if c in printable:
      out.append('   %c ' % c)
    else:
      out.append('0x%02x ' % ord(c))
  return ''.join(out)

def FormatAsBits(output_and_bits):
  """ Takes as input a tuple representing (array_of_bytes, number_of_bits),
  and formats it as binary, with byte-boundaries marked"""
  (output, bits) = output_and_bits
  retval = []
  if not bits:
    total_bits = len(output) * 8
  elif bits % 8:
    total_bits = (len(output) - 1) * 8 + (bits % 8)
  else:
    total_bits = len(output) * 8
  idx = 0
  while total_bits >= 8:
    c = output[idx]
    idx += 1
    retval.append('|')
    retval.append('{0:08b}'.format(c))
    total_bits -= 8

  if (bits % 8) != 0:
    retval.append('|')
    retval.append('{0:08b}'.format(output[idx])[0:(bits % 8)])
  retval.extend([' [%d]' % bits])
  return ''.join(retval)


class IDStore(object):
  """ Manages a store of IDs"""
  def __init__(self):
    self.ids = set()
    self.next_idx = 0

  def GetNext(self):
    """ Gets the next available ID. If an ID was returned, it will use that,
        else it will create a new unique id"""
    if self.ids:
      return self.ids.pop()
    self.next_idx += 1
    return self.next_idx

  def DoneWithId(self, id):
    """ Allows an ID to be reused later"""
    self.ids.add(id)


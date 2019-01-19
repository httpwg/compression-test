#!/usr/bin/env python

from collections import defaultdict
from copy import copy
from importlib import import_module
import os
import sys
from compressor import format_http1

# pylint: disable=W0311

def compare_headers_impl(a_input, b_input, ignores):
  def NormalizeDict(d):
    nd = set()
    for k,v in d.items():
      if k in ignores:
        continue
      if k == 'cookie':
        splitlist = set([x.strip(' ') for x in v.split(';')])
      else:
        splitlist = set([x.strip(' ') for x in v.split('\0')])
      for item in splitlist:
        nd.add( (k, item) )
    return nd

  a_hdr = NormalizeDict(a_input)
  b_hdr = NormalizeDict(b_input)
  retval = {'a_only': a_hdr.difference(b_hdr),
            'shared': a_hdr.intersection(b_hdr),
            'b_only': b_hdr.difference(a_hdr)}
  return retval


class Processors(object):
  """
  Contains the candidate processors that we want to compare.
  """
  module_dir = "compressor"

  def __init__(self, options, msg_types, output):
    self.options = options
    self.msg_types = msg_types
    self.output = output
    self.warned = {'http1_gzip': True}  # procs with no decompress support
    self.processors = self.get_processors(options.processor_names)

  def get_processors(self, processor_names):
    """
    Get a hash of codec names to processors.
    """
    procs = defaultdict(list)
    for name in processor_names:
      if "=" in name:
        module_name, param_str = name.split("=", 1)
        if param_str[0] == param_str[-1] == '"':
          param_str = param_str[1:-1]
        params = [param.strip() for param in param_str.split(',')]
      else:
        module_name = name
        params = []
      module = import_module("%s.%s" % (self.module_dir, module_name))
      procs['req'].append(module.Processor(self.options, True, params))
      procs['res'].append(module.Processor(self.options, False, params))
    return procs

  def process_session(self, session):
    """
    Process the messages in the session with all processors, and record
    results.
    """
    msg_idx = 0
    msg_tot = len(session.messages)
    self.processors = self.get_processors(self.options.processor_names)
    for (hdrs, host) in session.messages:
      msg_idx += 1
      results = self.process_message(hdrs, session.msg_type,
                                     host, msg_idx, msg_tot)
      for proc_name, resu in list(results.items()):
        if proc_name == self.options.baseline:
          ratio = 1.0
        else:
          ratio = 1.0 * resu['size'] / results[self.options.baseline]['size']
        session.record_result(proc_name, resu['size'], ratio, resu['time'])

  @staticmethod
  def filter_headers(hdrs):
    new_hdrs = {}
    ignore_hdrs = [':status-text', ':version', 'keep-alive', 'connection']
    if 'connection' in hdrs:
      ignore_hdrs.extend([x.strip(' ') for x in hdrs['connection'].split(',')])

    for k,v in hdrs.items():
      if k in ignore_hdrs:
        continue
      new_hdrs[k] = v
    return new_hdrs

  def process_message(self, hdrs, msg_type, host, msg_idx, msg_tot):
    """
    message is a HTTP header dictionary in the format described in
    compression.BaseProcessor.

    msg_type is 'req' or 'res'.

    host is the host header of the associated request.

    Returns a dictionary of processor names mapped to their results.
    """
    if self.options.verbose > 3:
      self.output('#' * 80)
      self.output('\n')
    results = {}
    for processor in self.processors[msg_type]:
      if self.options.verbose >= 3:
        self.output("# %s %s %d (of %d) for %s\n" %
            (processor.name,
             "request" if msg_type=="req" else "response",
             msg_idx,
             msg_tot,
             host))
      start_time = sum(os.times()[:2])
      filtered_hdrs = Processors.filter_headers(hdrs)

      compressed = processor.compress(filtered_hdrs, host)
      results[processor.name] = {
        'size': len(compressed),
        'time': sum(os.times()[:2]) - start_time
      }

      decompressed = None
      try:
        decompressed = processor.decompress(compressed)
      except NotImplementedError:
        if processor.name not in list(self.warned.keys()):
          sys.stderr.write(
            "  WARNING: %s decompression not checked.\n" % processor.name
          )
          self.warned[processor.name] = True
        continue
      if self.options.verbose > 3:
        if decompressed is not None:
          txt = format_http1(decompressed)
        else:
          txt = str(compressed, 'utf-8', 'replace') \
                .encode('utf-8', 'replace')
        self.output("%s" % txt)
        if not txt or txt[-1] != "\n":
          self.output("\n\n")
      compare_result = self.compare_headers(filtered_hdrs, "orig",
                                            decompressed, processor.name)
      if compare_result:
        self.output('  - mismatch in %s' % processor.name)
        if self.options.verbose > 1:
          self.output(':\n' + compare_result + "\n")
        self.output("\n")
        if self.options.debug:
            sys.exit(1)
    return results

  def done(self):
    for processor_kind in list(self.processors.values()):
      for processor in processor_kind:
        try:
          processor.done()
        except:
          pass

  @staticmethod
  def compare_headers(a_hdr, a_name, b_hdr, b_name):
    """
    Compares two dicts of headers, and returns a message denoting any
    differences. It ignores:
     - ordering differences in cookies
     - connection headers
     - HTTP version
     - HTTP status phrase
    If nothing is different, it returns an empty string. If it is, it
    returns a string explaining what is different.
    """
    ignores = [':version', ':status-text', 'connection']
    a_hdr = dict(a_hdr)
    b_hdr = dict(b_hdr)
    compare_result = compare_headers_impl(a_hdr, b_hdr, ignores)
    retval = []
    if compare_result['a_only']:
      retval.append('Only found in: %s' % a_name)
      for a_item in compare_result['a_only']:
        retval.append("\t%s: %s" % (a_item[0], a_item[1]))
    if compare_result['b_only']:
      retval.append('Only found in: %s' % b_name)
      for b_item in compare_result['b_only']:
        retval.append("\t%s: %s" % (b_item[0], b_item[1]))
    return '\n'.join(retval)

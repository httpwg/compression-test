#!/usr/bin/env python

"""
compression_test.py

Tests various HTTP header compression algorithms, to compare them.
"""

# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# pylint: disable=W0311

from collections import defaultdict
from importlib import import_module
import itertools
import locale
import optparse
import sys
import os.path
import fnmatch, re

import harfile

if os.name == "nt":
  locale.setlocale(locale.LC_ALL, 'english-us')
else:
  locale.setlocale(locale.LC_ALL, 'en_US')

class Connection(object):
  """
    A simulated http connection with its own set of header compressors
    """

  def __init__(self, name, compressors, glob):
    self.name = name
    self.compressors = compressors
    self.glob = glob
    self.patterns = []
    self.tlds = []
      
    for s in re.split('/', name):
      m = None
      if s.startswith('*'):
        self.patterns.append(re.compile(fnmatch.translate(s)))
        m = re.match('\*(.*\.)?([^.]+\.[^.]+)\.?', s)
      elif re.search('\\\.', s):
        self.patterns.append(re.compile(s))
        m = re.match('(.*\.)?([^.]+\.[^.]+)\.?', re.sub('\\\.', '.', s))
      elif self.glob:
        self.patterns.append(re.compile(fnmatch.translate('*'+s)))
        m = re.match('(.*\.)?([^.]+\.[^.]+)\.?', s)
      if m:
        self.tlds.append(m.group(2))

  def matches(self, host):
    
    if True in itertools.ifilter(lambda x: x.match(host), self.patterns):
      return True
    if True in itertools.imap(host.endswith, self.tlds):
      return True
    return self.name == host




class CompressionTester(object):
  """
  This is the thing.
  """
  msg_types = ['req', 'res']
  
  def __init__(self):
    self.output = sys.stdout.write
    self.warned = {'http1_gzip': True}  # procs with no decompress support
    self.tsv_out = defaultdict(list)  # accumulator for TSV output
    self.ttls = None
    self.lname = 0  # longest processor name
    self.options, self.args = self.parse_options()
    self.codec_modules, self.codec_params = self.get_compressor_modules()
    self.connections = self.init_connections()
    self.run()

      
  def run(self):
    "Let's do this thing."
    messages = []
    for filename in self.args:
      har_requests, har_responses = harfile.read_har_file(filename)
      both = zip(har_requests, har_responses)
      for req, res in both:
        messages.append(('req', req, req[':host']))
        messages.append(('res', res, req[':host']))
    self.ttls = self.process_messages(messages)
    self.output("%i connections simulated to different hosts\n" % (len(self.connections.keys())))
    for msg_type in self.msg_types:
      self.print_results(self.ttls.get(msg_type, {}), msg_type, True)
    if self.options.tsv:
      self.output_tsv()
      
    
  def process_messages(self, messages):
    "Process some messages."
    if len(messages) == 0:
      sys.stderr.write("Nothing to process.\n")
      return {}
    
    ttls = dict([(msg_type, defaultdict(lambda:{
      'size': 0,
      'maxr': 0,
      'minr': 1e20,
      'ratio_list': [],
    })) for msg_type in self.msg_types])
    
    for (message_type, message, host) in messages:
      results = self.process_message(message, message_type, host)
      for name, result in results.items():
        if name[0] == "_": 
          continue
        target = ttls[message_type][name]
        target['size'] += result['size']
        target['maxr'] = max(target['maxr'], result['ratio'])
        target['minr'] = min(target['minr'], result['ratio'])
        target['ratio_list'].append(result['ratio'])
      ttls[message_type]['_num'] = len(messages)
    
    for message_type in self.msg_types:
      baseline_ratio = ttls[message_type][self.options.baseline]['size']
      for name, result in ttls[message_type].items():
        if name[0] == "_":
          continue
        result['ratio'] = 1.0 * result['size'] / baseline_ratio
        result['std'] = self.meanstdv(result['ratio_list'])[1]

    return ttls

  
  def process_message(self, message, message_type, host):
    """
    message is a HTTP header dictionary in the format described in
    compression.BaseProcessor.
    
    message_type is 'req' or 'res'.
    
    host is the host header of the associated request.
    Returns a dictionary of processor names mapped to their results.
    Items in the dictionary whose names start with "_" are metadata.
    """
    connection = self.get_connection(host)
    procs = [
      (name, proc[self.msg_types.index(message_type)]) for name, proc in \
        connection.compressors.items()
    ]
    results = {"_message_type": message_type}
    for name, processor in procs:
      compressed = processor.compress(message, host)
      if self.options.verbose > 2:
        txt = unicode(compressed, 'utf-8', 'replace') \
              .encode('utf-8', 'replace')
        self.output("\n# %s\n%s\n\n" % (name, txt)) 
      decompressed = None
      try:
        decompressed = processor.decompress(compressed)
      except NotImplementedError:
        if name not in self.warned.keys():
          sys.stderr.write("WARNING: %s decompression not checked.\n" % name)
          self.warned[name] = True
      if decompressed:
        compare_result = self.compare_headers(message, decompressed)
        if compare_result:
          sys.stderr.write('*** COMPRESSION ERROR in %s.\n' % name)
          if self.options.verbose >= 1:
            self.output(compare_result + "\n\n")
      
      results[name] = {
        'compressed': compressed,
        'decompressed': decompressed,
        'size': len(compressed)
      }

    if self.options.baseline in results.keys():
      baseline_size = results[self.options.baseline]['size']
      if baseline_size > 0:
        for name, result in results.items():
          if name[0] == "_": 
            continue
          result['ratio'] = 1.0 * result['size'] / baseline_size

    if self.options.tsv:
      self.tsv_results(results, connection)

    if self.options.verbose >= 2 and not self.options.tsv:
      self.print_results(results, message_type)

    return results

  
  def print_results(self, results, message_type, stats=False):
    """
    Output a summary of the results. Expects results to be the dictionary
    format described in compression.BaseProcessor.
    """
    
    if stats:
      self.output("%i %s messages processed\n" %
        (results['_num'], message_type))
    
    codecs = [name for name in results.keys() if name[0] != "_"]
    codecs.sort()    
    lines = []
    for name in codecs:
      ratio = results[name].get('ratio', 0)
      compressed_size = results[name].get('size', 0)
      pretty_size = locale.format("%13d", compressed_size, grouping=True)
      if stats:
        minr = results[name].get('minr', 0)
        maxr = results[name].get('maxr', 0)
        std = results[name]['std']
        lines.append(
          (message_type, name, pretty_size, ratio, minr, maxr, std)
        )
      else:
        lines.append((message_type, name, pretty_size, ratio))
    
    if stats:
      self.output(
        '%%%ds        compressed | ratio min   max   std\n' % self.lname % ''
      )
      fmt = '%%s %%%ds %%s | %%2.2f  %%2.2f  %%2.2f  %%2.2f\n' % self.lname
    else:
      self.output('%%%ds        compressed | ratio\n' % self.lname % '')
      fmt = '%%s %%%ds %%s | %%2.2f\n' % self.lname
    for line in sorted(lines):
      self.output(fmt % line)

    self.output("\n")
    if self.options.verbose > 1 and not stats:
      self.output("-" * 80 + "\n")
        

  def tsv_results(self, results, connection):
    """
    Store TSV; takes a record number and a results object.
    """
    items = ["%i"]
    codecs = [name for name in results.keys() if name[0] != "_"]
    codecs.sort()
    for name in codecs:
      items.append(results[name].get('size', 0))
    message_type = results["_message_type"]
    
    if len(self.tsv_out[message_type]) == 0:
      self.tsv_out[message_type].append("num\t" + "\t".join(codecs) + "\tconnection\n")
    
    self.tsv_out[message_type].append(
      "%s\t%s\n" % ("\t".join([str(item) for item in items]), connection.name)
    )


  def output_tsv(self):
    "Write stored TSV to files."
    for message_type, lines in self.tsv_out.items():
      tfh = open("%s%s" % (self.options.prefix, "%s.tsv" % message_type), 'w')
      count = 0
      for line in lines:
        if count == 0:
          tfh.write(line)
        else:
          tfh.write(line % count)
        count += 1
      tfh.close()


  def get_compressor_modules(self):
    """
      Get a hash of codec names to modules.
      Get a hash of codec names to codec params.
      """
    codec_modules = {}
    codec_params = {}
    for codec in self.options.codec:
      if "=" in codec:
        module_name, param_str = codec.split("=", 1)
        if param_str[0] == param_str[-1] == '"':
          param_str = param_str[1:-1]
        params = [param.strip() for param in param_str.split(',')]
      else:
        module_name = codec
        params = []
      if len(module_name) > self.lname:
        self.lname = len(module_name)
      codec_modules[module_name] = import_module("compressor.%s" % module_name)
      codec_params[module_name] = params
    return codec_modules, codec_params
  
  def get_compressors(self):
    """
      Get a fresh initialed set of compressor codecs
      """
    compressors = {}
    for name, module in self.codec_modules.items():
      params = self.codec_params[name]
      compressors[name] = ( # same order as self.msg_types
                           module.Processor(self.options, True, params),
                           module.Processor(self.options, False, params)
                           )
    return compressors
  
  def get_connection(self, host):
    """
      Get the name of the connection used for talking to a certain host.
      """
    if host in self.connections:
      return self.connections[host]
    
    for c in self.connections.values():
      if c.matches(host):
        return c
  
    conn = Connection(host, self.get_compressors(), self.options.glob)
    self.connections[host] = conn
    if self.options.verbose > 0:
      print 'new connection %s [%s]' % (conn.name, ', '.join(conn.tlds))
  
    return conn

  def init_connections(self):
    connections = {}
    for pattern in self.options.multiplex:
      connections[pattern] = Connection(pattern, self.get_compressors(), self.options.glob)
    if self.options.verbose > 0:
      for conn in connections.values():
        print 'initial connection %s [%s]' % (conn.name, ', '.join(conn.tlds))
    return connections
  
  @staticmethod
  def parse_options():
    "Parse command-line options and return (options, args)."
    optp = optparse.OptionParser()
    optp.add_option('-v', '--verbose',
                  type='int',
                  dest='verbose',
                  help='set verbosity, 1-5 (default: %default)',
                  default=0,
                  metavar='VERBOSITY')
    optp.add_option('-c', '--codec',
                  action='append',
                  dest='codec',
                  help='compression modules to test, potentially with '
                  'parameters. '
                  'e.g. -c spdy3 -c fork="abc" '
                  '(default: %default)',
                  default=['http1'])
    optp.add_option('-b', '--baseline',
                  dest='baseline',
                  help='baseline codec to base comparisons upon. '
                  '(default: %default)',
                  default='http1')
    optp.add_option('-m', '--multiplex',
                  action='append',
                  dest='multiplex',
                  metavar='PATTERN[/PATTERN]',
                  help='multiplex matching hosts onto same connection. '
                  'e.g. -m *yahoo.com,*.yimg.com ("-m *" to simulate a single'
                  ' connection, PATTERN is a UNIX filename pattern or '
                  'a regex containing \. or simply a string. Separate multiple '
                  'patterns for the same connection by /)',
                  default=[])
    optp.add_option('-n', '--noglob',
                  action='store_false',
                  dest='glob',
                  help='do not reuse connections for hosts in the same top level '
                  'domain. Otherwise a connection to www1.exmple.org is also used '
                  'for www2.example.org.',
                  default=True)
    optp.add_option('-t', '--tsv',
                  action="store_true",
                  dest="tsv",
                  help="output TSV.",
                  default=False)
    optp.add_option('--prefix',
                  action="store",
                  dest="prefix",
                  help="Prefix for TSV file output.",
                  default="")
    return optp.parse_args()

  
  @staticmethod
  def compare_headers(a_hdr, b_hdr):
    """
    Compares two dicts of headers, and returns a message denoting any
    differences. It ignores ordering differences in cookies, but tests that
    all the content does exist in both.
    If nothing is different, it returns an empty string.
    """
    output = []
    for d_hdr in [a_hdr, b_hdr]:
      if 'cookie' in d_hdr.keys():
        splitvals = d_hdr['cookie'].split(';')
        d_hdr['cookie'] = \
          '; '.join(sorted([x.lstrip(' ') for x in splitvals]))
    for (key, val) in a_hdr.iteritems():
      if key in [':version', ':status-text']:
        pass
      elif not key in b_hdr:
        output.append('\t%s present in only one (A)' % key)
        continue
      elif val.strip() != b_hdr[key].strip():
        output.append('\t%s has mismatched values:' % key)
        output.append('\t  a -> %s' % val)
        output.append('\t  b -> %s' % b_hdr[key])
      del b_hdr[key]
    for key in b_hdr.keys():
        output.append('\t%s present in only one (B)' % key)
    return '\n'.join(output)


  @staticmethod
  def meanstdv(members):
    """
    Calculate mean and standard deviation of data x[]:
        mean = {\sum_i x_i \over n}
        std = sqrt(\sum_i (x_i - mean)^2 \over n-1)
    """
    from math import sqrt
    num, mean, std = len(members), 0, 0
    for item in members:
      mean = mean + item
    mean = mean / float(num)
    for item in members:
      std = std + (item - mean)**2
    std = sqrt(std / float(num - 1))
    return mean, std


if __name__ == "__main__":
  CompressionTester()

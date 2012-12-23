#!/usr/bin/env python

# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from collections import defaultdict
from importlib import import_module
import locale
import optparse
import re
import sys

import harfile

locale.setlocale(locale.LC_ALL, 'en_US')

class CompressionTester(object):
  msg_types = ['req', 'res']
  
  def __init__(self):
    self.output = sys.stdout.write
    self.lname = 0
    self.options, self.args = self.parse_options()
    self.codec_processors = self.get_codecs()
    messages = self.get_messages()
    self.ttls = self.process_messages(messages)
    if self.options.verbose >= 1:
      self.output("=" * 80 + "\n\n")
    for msg_type in self.msg_types:
      self.print_results(self.ttls.get(msg_type, {}), msg_type, True)


  def get_messages(self):
    "Return a list of (message_type, message, host)."
    messages = []
    for filename in self.args:
      har_requests, har_responses = harfile.ReadHarFile(filename)
      reqs = [('req', msg, msg[':host']) for msg in har_requests]
      messages.extend(reqs)
      #FIXME
      messages.extend([('res', msg, 'foo') for msg in har_responses])
    return messages


  def process_messages(self, messages):
    "Let's do this thing."
    if len(messages) == 0:
      sys.stderr.write("Nothing to process.\n")
      return {}

    ttls = dict([(msg_type, defaultdict(lambda:{
      'size': 0,
      'maxr': 0,
      'minr': 1e20
    })) for msg_type in self.msg_types])

    for (message_type, message, host) in messages:
      results = self.process_message(message, message_type, host)
      for name, result in results.items():
        target = ttls[message_type][name]
        target['size'] += result['size']
        target['maxr'] = max(target['maxr'], result['ratio'])
        target['minr'] = min(target['minr'], result['ratio'])
      ttls[message_type]['_num'] = len(messages)

    for message_type in self.msg_types:
      baseline_ratio = ttls[message_type][self.options.baseline]['size']
      for name, result in ttls[message_type].items():
        if name[0] == "_": 
          continue
        result['ratio'] = 1.0 * result['size'] / baseline_ratio
    return ttls


  def process_message(self, message, message_type, host):
    """
    This uses the various different processor classes to compress,
    potentially report on the results of each, and then accumulates stats on
    the effectiveness of each.

    Returns a dictionary of processor names mapped to their results.
    """
    procs = [
      (name, proc[self.msg_types.index(message_type)]) for name, proc in \
       self.codec_processors.items()
    ]
    results = {}
    for name, processor in procs:
      result = processor.compress(message, host)
      results[name] = {
        'compressed': result,
        'size': len(result)      
      }
    if self.options.baseline in results.keys():
      baseline_size = results[self.options.baseline]['size']
      if baseline_size > 0:
        for name, result in results.items():
          result['ratio'] = 1.0 * result['size'] / baseline_size
    if self.options.verbose >= 1:
      self.print_results(results, message_type)
    return results


  def print_single(self, name, result):
    "Print details of a singe message."
    if self.options.verbose >= 1:
      print ('\t%% %ds              UC  |  CM  | ratio' % (
             self.lname + 10)) % ''
      line_format = '\t%% %ds frame size: %%4d | %%4d | %%2.2f ' % (
          self.lname + 10)
      for line in sorted(lines):
        print line_format % line
      print

      if 'output_headers' in result: #FIXME
        output_headers = result['output_headers']
        compare_result = self.compare_headers(message, output_headers)
        if compare_result:
          print 'Something is wrong with this frame.'
          if self.options.verbose >= 1:
            print compare_result
          if self.options.verbose >= 5:
            print 'It should be:'
            for k,v in        request.iteritems(): print '\t%s: %s' % (k,v)
            print 'but it was:'
            for k,v in output_headers.iteritems(): print '\t%s: %s' % (k,v)


  def print_results(self, results, message_type, stats=False):
    """
    Output a summary of the results. Expects results to be the dictionary
    format described in compression.BaseProcessor.
    """

    if self.options.verbose >= 2:
      self.output("\n" + ("-" * 80) + "\n")    
    if stats:
      self.output("%i %s messages processed\n" % 
        (results['_num'], message_type))
    
    codecs = results.keys()
    codecs.sort()

    lines = []
    for name in codecs:
      if name[0] == "_":
        continue
      ratio = results[name].get('ratio', 0)
      compressed_size = results[name].get('size', 0)
      pretty_size = locale.format("%13d", compressed_size, grouping=True)
      if stats:
        minr = results[name].get('minr', 0)
        maxr = results[name].get('maxr', 0)
        lines.append((message_type, name, pretty_size, ratio, minr, maxr))
      else:
        lines.append((message_type, name, pretty_size, ratio))

    if stats:
      self.output('%%%ds        compressed | ratio min   max\n' % self.lname % '')
      format = '%%s %%%ds %%s | %%2.2f  %%2.2f  %%2.2f\n' % self.lname
    else:
      self.output('%%%ds        compressed | ratio\n' % self.lname % '')
      format = '%%s %%%ds %%s | %%2.2f\n' % self.lname
    for line in sorted(lines):
      self.output(format % line)
    self.output("\n")


  def get_codecs(self):
    """
    Get a hash of codec names to processors.
    """
    codec_processors = {}
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
      module = import_module("compression.%s" % module_name)
      codec_processors[module_name] = ( # same order as self.msg_types
        module.Processor(self.options, True, params),
        module.Processor(self.options, False, params)
      )
    return codec_processors


  def parse_options(self):
    "Parse command-line options and return (options, args)."
    op = optparse.OptionParser()
    op.add_option('-v', '--verbose',
                  type='int',
                  dest='verbose',
                  help='set verbosity, 1-5 (default: %default)',
                  default=0,
                  metavar='VERBOSITY')
    op.add_option('-c', '--codec',
                  action='append',
                  dest='codec',
                  help='compression modules to test, potentially with '
                  'parameters. '
                  'e.g. -c spdy3 -c fork="abc" '
                  '(default: %default)',
                  default=['http1'])
    op.add_option('-b', '--baseline',
                  dest='baseline',
                  help='baseline codec to base comparisons upon. '
                  '(default: %default)',
                  default='http1')
    return op.parse_args()


  @staticmethod
  def compare_headers(a, b):
    """
    Compares two sets of headers, and returns a message denoting any
    differences. It ignores ordering differences in cookies, but tests that all
    the content does exist in both.
    If nothing is different, it returns an empty string.
    """
    a = dict(a)
    b = dict(b)
    output = []
    if 'cookie' in a:
      splitvals = a['cookie'].split(';')
      a['cookie'] = '; '.join(sorted([x.lstrip(' ') for x in splitvals]))
    if 'cookie' in b:
      splitvals = b['cookie'].split(';')
      b['cookie'] = '; '.join(sorted([x.lstrip(' ') for x in splitvals]))
    for (k,v) in a.iteritems():
      if not k in b:
        output.append('\tkey: %s present in only one (A)' % k)
        continue
      if v != b[k]:
        output.append('\tkey: %s has mismatched values:' % k)
        output.append('\t  -> %s' % v)
        output.append('\t  -> %s' % b[k])
      del b[k]
    for (k, v) in b.iteritems():
        output.append('\tkey: %s present in only one (B)' % k)
    return '\n'.join(output)


if __name__ == "__main__":
  CompressionTester()
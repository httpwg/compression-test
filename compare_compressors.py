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
import locale
import optparse
import operator
from functools import reduce

from lib.harfile import read_har_file
from lib.processors import Processors


class CompressionTester(object):
  """
  This is the thing.
  """
  msg_types = ['req', 'res']
  streamifier_dir = "lib.streamifiers"

  def __init__(self, output):
    self.options, self.args = self.parse_options()
    if self.options.baseline is None:
      self.options.baseline = "http1"
    if not self.options.baseline in self.options.processor_names:
      new_processor_names = [self.options.baseline]
      new_processor_names.extend(self.options.processor_names)
      self.options.processor_names = new_processor_names
    self.output = output
    self.tsv_out = defaultdict(list)  # accumulator for TSV output
    self.processors = Processors(self.options, self.msg_types, output)
    self.streamify = self.load_streamifier(self.options.streamifier)
    self.run()

  def run(self):
    "Let's do this thing."
    sessions = []
    for filename in self.args:
      har_requests, har_responses = read_har_file(filename)
      messages = list(zip(har_requests, har_responses))
      sessions.extend(self.streamify(messages))
    for session in sessions:
      if self.options.verbose > 0:
        session.print_header(self.output)
      self.processors.process_session(session)
      if self.options.verbose > 0:
        session.print_summary(self.output, self.options.baseline)
    self.processors.done()
    for msg_type in self.msg_types:
      ttl_stream = reduce(operator.add, [s for s in sessions if s.msg_type == msg_type])
      ttl_stream.name = "TOTAL"
      ttl_stream.print_header(self.output)
      ttl_stream.print_summary(self.output, self.options.baseline)
    if self.options.tsv:
      out = {}
      for msg_type in self.msg_types:
        out[msg_type] = [
          open("%s%s" % (self.options.prefix, "%s.tsv" % msg_type), 'w'),
          0
        ]
        sessions[0].print_tsv_header(out[msg_type][0].write)
      for session in sessions:
        tsvfh, tsv_count = out[session.msg_type]
        out[session.msg_type][1] = session.print_tsv(tsvfh.write, tsv_count)
      for fh, count in list(out.values()):
        fh.close()

  def load_streamifier(self, name):
    "Load the streamifier specified in the options."
    return import_module("%s.%s" % (self.streamifier_dir, name)) \
      .Streamifier([p.name for p in self.processors.processors['req']]) \
      .streamify

  def parse_options(self):
    "Parse command-line options and return (options, args)."
    optp = optparse.OptionParser()
    optp.add_option('-v', '--verbose',
                  type='int',
                  dest='verbose',
                  help='set verbosity, 1-5 (default: %default)',
                  default=0,
                  metavar='VERBOSITY')
    optp.add_option('-d', '--debug',
                  action='store_true',
                  dest="debug",
                  help="debug mode. Stops on first header mismatch.",
                  default=False)
    optp.add_option('-c', '--codec',
                  action='append',
                  dest='processor_names',
                  help='compression modules to test, potentially with '
                  'parameters. '
                  'e.g. -c spdy3 -c fork="abc" '
                  '(default: %default)',
                  default=[])
    optp.add_option('-b', '--baseline',
                  dest='baseline',
                  help='baseline codec to base comparisons upon. '
                  '(default: %default)',
                  default=None)
    optp.add_option('-t', '--tsv',
                  action="store_true",
                  dest="tsv",
                  help="output TSV.",
                  default=False)
    optp.add_option('-s', '--streamifier',
                  dest="streamifier",
                  help="streamifier module to use (default: %default).",
                  default="public_suffix")
    optp.add_option('--prefix',
                  action="store",
                  dest="prefix",
                  help="Prefix for TSV file output.",
                  default="")
    return optp.parse_args()


if __name__ == "__main__":
  import os
  import sys
  if os.name == "nt":
    locale.setlocale(locale.LC_ALL, 'english-us')
  else:
    locale.setlocale(locale.LC_ALL, 'en_US')
  CompressionTester(sys.stdout.write)

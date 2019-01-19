#!/usr/bin/env python

from collections import defaultdict
import locale

# pylint: disable=W0311


class Stream(object):
  """
  A one-way stream of sets of HTTP headers.
  
  For our purposes, a stream is the unit that gets compressed; i.e., the
  headers in it have a shared context.
  """
  def __init__(self, name, messages, msg_type, procs):
    self.name = name # identifier for the stream; e.g., "example.com reqs"
    self.messages = messages
    self.msg_type = msg_type # "req" or "res"
    self.procs = procs # order of processors
    self.lname = max([len(p) for p in procs]) # longest processor name
    self.sizes = defaultdict(list)
    self.ratios = defaultdict(list)
    self.times = defaultdict(list)

  def record_result(self, proc_name, size, ratio, time):
    "Record the results of processing, by proc_name."
    self.sizes[proc_name].append(size)
    self.ratios[proc_name].append(ratio)
    self.times[proc_name].append(time)

  def print_header(self, output):
    "Print a header for the summary to output."
    output("* %s: %i %s messages\n" %
      (self.name, len(self.messages), self.msg_type))

  def print_summary(self, output, baseline):
    "Print a summary of the stream to output, compared to baseline."
    lines = []
    baseline_size = sum(self.sizes[baseline])
    for proc in self.procs:
      ttl_size = sum(self.sizes[proc])
      ttl_time = sum(self.times[proc])
      pretty_size = locale.format("%13d", ttl_size, grouping=True)
      ratio = 1.0 * ttl_size / baseline_size
      try:
        std = meanstdv(self.ratios[proc])[1]
      except ZeroDivisionError:
        std = 0
      min_ratio = min(self.ratios[proc])
      max_ratio = max(self.ratios[proc])
      lines.append((proc, pretty_size, ttl_time, ratio, min_ratio, max_ratio, std))
    output('  %%%ds size  time | ratio min   max   std\n' % (self.lname + 9) % '')
    fmt = '  %%%ds %%s %%5.2f | %%2.2f  %%2.2f  %%2.2f  %%2.2f\n' % self.lname
    for line in lines:
      output(fmt % line)
    output("\n")

  def print_tsv_header(self, output):
    "Print a TSV header to output."
    header = "\t".join(["num", "name"] + self.procs)
    output("%s\n" % header)

  def print_tsv(self, output, count=0):
    "Print the stream as TSV to output, using count as a counter."
    lines = list(zip(*[self.sizes[proc] for proc in self.procs]))
    for line in lines:
      count += 1
      output("\t".join([str(count), self.name] + [str(j) for j in line]))
      output("\n")
    return count

  def __add__(self, other):
    assert self.msg_type == other.msg_type
    new = Stream('', self.messages, self.msg_type, self.procs)
    new.messages.extend(other.messages) # NB: not great for memory
    new.sizes = merge_dols(self.sizes, other.sizes)
    new.ratios = merge_dols(self.ratios, other.ratios)
    new.times = merge_dols(self.times, other.times)
    new.procs = self.procs
    new.lname = self.lname
    return new
    
  def __radd__(self, other):
    new = Stream('', self.messages, self.msg_type, self.procs)
    new.sizes = self.sizes
    new.ratios = self.ratios
    new.times = self.times
    new.procs = self.procs
    new.lname = self.lname
    return new


def merge_dols(dol1, dol2):
  """
  Merge two dictionaries of lists.
  """
  result = dict(dol1, **dol2)
  result.update((k, dol1[k] + dol2[k])
                for k in set(dol1).intersection(dol2))
  return result
    
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
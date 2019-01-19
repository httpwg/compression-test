#!/usr/bin/python

"""
Utilities to get harfiles into the shape we want them to be.
"""

# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# pylint: disable=W0311

import re
import json
import sys
from urllib.parse import urlsplit

def read_har_file(filename):
  "Read filename and return the header dictionaries for it."
  fhandle = open(filename)
  try:
    har = json.loads(fhandle.read())
  except Exception as oops:
    sys.stderr.write("Unable to parse %s\n\n" % filename)
    sys.stderr.write(oops)
    sys.exit(1)
  finally: 
    fhandle.close()
  return har2hdrs(har)


def har2hdrs(har):
  """
  Convert a har dictionary to two lists of header dictionaries for requests
  and responses.
  
  Headers derived from other information are preceded by a ":" character.
  """
  request_headers = []
  response_headers = []
  for entry in har["log"]["entries"]:
    request = entry["request"]
    url = urlsplit(request["url"])
    if not url.scheme.lower() in ["http", "https"]:
      continue
    headers = process_headers(request["headers"])
    headers[":method"] = request["method"].lower()
    headers[":path"] = url.path
    if url.query:
      headers[":path"] += "?%s" % url.query
    headers[":scheme"] = url.scheme.lower()
    headers[":version"] = request["httpVersion"]
    if not ":host" in request_headers:
      headers[":host"] = re.sub("^[^:]*://([^/]*)/.*$", "\\1", request["url"])
    request_headers.append(headers)

    response = entry["response"]
    headers = process_headers(response["headers"])
    headers[":status"] = re.sub("^([0-9]*).*", "\\1", str(response["status"]))
    headers[":status-text"] = response["statusText"].strip() or \
      STATUS_PHRASES.get(headers[':status'], 'unknown')
    headers[":version"] = response["httpVersion"]
    response_headers.append(headers)

  return (request_headers, response_headers)


def process_headers(hdrdicts):
  "Take a har header datastructure and return a normalised dictionary."
  out = {}
  for hdrdict in hdrdicts:
    name = hdrdict["name"].lower()
    val = hdrdict["value"]
    if not name:
      raise Exception()
    if name == "host":
      name = ":host"
    if name in out:
      out[name] = out[name] + '\0' + val
    else:
      out[name] = val
  return out

def encode_strings(inobj, encoding="latin-1"):
  "Encode strings in objects. Latin-1 is the default encoding for HTTP/1.x."
  retval = {}
  for key, val in inobj.items():
    if key in ['text', 'content']:
      continue
    else:
      n_k = key
      if isinstance(key, str):
        n_k = key.encode(encoding)
      n_v = val
      if isinstance(val, str):
        n_v = val.encode(encoding)
      retval[n_k] = n_v
  return retval


STATUS_PHRASES = {
  '200': 'OK',
  '201': 'Created',
  '202': 'Accepted',
  '203': 'Non-Authoritative Information',
  '204': 'No Content',
  '205': 'Reset Content',
  '206': 'Partial Content',
  '207': 'Multi-Status',
  '300': 'Multiple Choices',
  '301': 'Moved Permanently',
  '302': 'Found',
  '303': 'See Other',
  '304': 'Not Modified',
  '307': 'Temporary Redirect',
  '308': 'Permanent Redirect',
  '400': 'Bad Request',
  '401': 'Unauthorized',
  '403': 'Forbidden',
  '404': 'Not Found',
  '405': 'Method Not Allowed',
  '406': 'Not Acceptable',
  '408': 'Request Timeout',
  '409': 'Conflict',
  '410': 'Gone',
  '500': 'Internal Server Error',
}


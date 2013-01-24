// Copyright (c) 2012 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
#include <iostream>
#include <stdlib.h>

#include "header_freq_tables.h"
#include "huffman.h"

using std::cerr;
using std::string;

struct Testcase {
  string input;
};

template <typename T>
void Test(const T& expected, const T& actual) {
  if (expected != actual) {
    cerr << "\n";
    cerr << "       --- FAILED ---\n";
    cerr << "   Expected: \"" << expected << "\"\n";
    cerr << "        Got: \"" << actual << "\"\n";
    abort();
  }
}

void TestEncodeDecode(const Huffman& huff,
                      const string& input,
                      bool use_eof,
                      bool use_length,
                      int length_delta) {
  string decoded;


  BitBucket bb;
  huff.Encode(&bb, input, use_eof);

  int num_bits = 0;
  if (use_length)
    num_bits = bb.NumBits() + length_delta;
  huff.Decode(&decoded, &bb, use_eof, num_bits);
  Test(input, decoded);
}

int main(int argc, char**argv) {
  Huffman huff;
  huff.Init(FreqTables::request_freq_table);
  array<string,6> tests = {{
    "dabbcccddddeeeee",
    "foobarbaz",
    "0-2rklnsvkl;-23kDFSi01k0=",
    "-9083480-12hjkadsgf8912345kl;hjajkl;       `123890",
    "-3;jsdf",
    "\xFF\xE0\t\ne\x81\x82",
  }};
  for (unsigned int i = 0; i < tests.size(); ++i) {
    const string& test = tests[i];
    cerr << "TEST: " << test << "...";
    cerr << "\n";
    TestEncodeDecode(huff, test,  true, false, 0);
    TestEncodeDecode(huff, test, false,  true, 0);
    TestEncodeDecode(huff, test,  true,  true, 8);
    cerr << "PASSED!\n";
  }
  //cout << huff;
  return EXIT_SUCCESS;
}

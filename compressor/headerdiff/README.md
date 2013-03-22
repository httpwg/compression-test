HeaderDiff Codec
================

Specification
-------------
The specification for the HeaderDiff codec is at:
https://datatracker.ietf.org/doc/draft-ruellan-headerdiff/

Delta-encoding modifications
----------------------------
The implementation support three modes for delta-encoding header values. In
addition, delta-encoding can be disabled.

The *full* mode searches for the largest shared prefix between the reference value and the value to encode.

The *bounded* mode limits the shared prefix, forcing it to end with a character contained in a list of limit characters. For example: `/?= ,`.

The *limit* mode limits the number of times an indexed value can be used as a reference for delta-encoding another value.

Huffman
-------
The implementation now optionally supports a static Huffman encoding for string
values.

Usage
-----

The HeaderDiff codec supports the following options:

- `buffer` for defining the maximum buffer size (default is 32768 bytes).
- `deflate` for specifying the windowSize for Deflate. It is an integer between
  8 and 15. By default, Deflate is not enabled.
- `delta` for enabling or disabling delta-encoding (shared prefix). Enabled by
  default.
- `delta_type` for specifying which type of delta-encoding to use.
  - *Full* mode: an empty value means that full prefix search is enabled.
  - *Bounded* mode: a string (possibly quoted) containing the characters
    defining the possible boundaries for the shared prefix.
  - *Limit* mode: an integer defining the maximum number of usage of an indexed
    value as a reference for delta-encoding another value.
- `huffman` for enabling Huffman encoding of string values. Disabled by default. 
  
Examples
--------

Using the default HeaderDiff codec:

    ./compare_compressors.py -c headerdiff file.har
    
Using HeaderDiff with a small buffer:

    ./compare_compressors.py -c "headerdiff=buffer=4096" file.har
    
Using HeaderDiff with Deflate:

    ./compare_compressors.py -c "headerdiff=deflate=12" file.har
    
Using both a small buffer and Deflate:

    ./compare_compressors.py -c "headerdiff=buffer=4096,deflate=12" file.har

Using HeaderDiff without delta-encoding:

    ./compare_compressors.py -c "headerdiff=delta=false" file.har

Using HeaderDiff with *bounded* delta-encoding:

    ./compare_compressors.py -c "headerdiff=delta_type='/?= \coma'" file.har

Using HeaderDiff with *limited* delta-encoding:

    ./compare_compressors.py -c "headerdiff=delta_type=2" file.har

Using HeaderDiff with a static Huffman encoding of strings:

    ./compare_compressors.py -c "headerdiff=huffman" file.har


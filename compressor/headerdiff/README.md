HeaderDiff Codec
================

Usage
-----

The HeaderDiff codec supports the following options:

- `buffer` for defining the maximum buffer size (default is 32768 bytes).
- `deflate` for specifying the windowSize for Deflate. It is an integer between
  8 and 15. By default, Deflate is not enabled.
  
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

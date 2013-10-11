HPACK Codec
===========

Specification
-------------
This codec is an implementation of HPACK (Header Compression for HTTP/2.0) which specification can be found at:
https://datatracker.ietf.org/doc/draft-ietf-httpbis-header-compression/. More specifically, this codec implements the 3rd draft of this specification.

Contents
--------
The codec comprises both an encoder and a decoder. It has a few options.

### Maximum buffer size

The buffer_size option allows to specify the maximum size of the header table.
The default value is 4096 bytes.

Example usage: 

	./compare_compressors.py -c "http2=buffer_size=8192" file.har

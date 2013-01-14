#!/usr/bin/env bash

compile() {
  file=$1
  site=$( basename $file .har )

  ./compare_compressors.py -t -c http1_gzip -c spdy3 -c delta \
    --prefix "$site". $file &&
  mv "$site"*tsv results
}

for i in $*; do
  compile $i
done
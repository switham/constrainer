#!/bin/sh
# examples/soma_do_all.sh -- Try to solve examples/soma_puzzles/*.spz puzzles.
#
#   Copyright (c) 2013 Steve Witham All rights reserved.  
#   Constrainer is available under a BSD license, whose full text is at
#       http://github.com/switham/constrainer/blob/master/LICENSE

if [ "$1" = "" ]; then
  dg="--default_guess True"
 else
  dg="--default_guess $1"
 fi

trap 'exit 1;' INT

for f in soma_puzzles/*.spz; do
  echo "===== $f ====="
  ./soma.py --puzzle $f $dg 2>&1 |while read line; do
    echo "    $line"
   done
  echo " "
 done
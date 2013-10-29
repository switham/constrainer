#!/bin/sh
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
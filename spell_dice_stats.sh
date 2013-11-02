if [ "$1" = "-f" ]; then
  f="$1"; shift
 else
  f=/tmp/spell_dice.out
  phrase=nowallcertainmov
  time ./spell_dice.py -c -m -v $phrase >"$f"
 fi
echo " "
grep "===== pop " "$f" |sort -n --key=3 |uniq -c
echo " "
tail -2 "$f"
echo $(grep try "$f" |wc -l) guesses
echo " "
grep "===== solution " "$f"|sort -n --key=4 |uniq -f 3 -c
echo "$f"

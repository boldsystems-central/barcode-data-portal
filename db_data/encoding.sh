#!bin/bash
echo "Encoding files to UTF-8"
for f in *.jsonl
do
    encoding=`file -I $f | cut -d ";" -f 2 | cut -d"=" -f 2`
    # TODO add more encodings as need be
    if [ $encoding == 'iso-8859-1' ]; 
    then 
    iconv -f $encoding -t UTF-8 $f > $f.utf8
    # mv $f.utf8 $f
    fi
done
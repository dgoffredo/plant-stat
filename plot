#!/bin/sh

set -e

days=${1:-0.5}
pic=${2:-data.png}

sqlite3 db.sqlite <<END_DB_COMMANDS
.mode columns
.headers off
.output dump.txt

select * from reading
where julianday() - julianday(when_iso) <= $days
order by when_iso;
END_DB_COMMANDS

gnuplot -e "output_file='$pic'" plant.plt
mv "$pic" /var/www/lookatmyplants.com/


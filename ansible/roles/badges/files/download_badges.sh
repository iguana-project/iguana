#!/bin/bash
: '
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
'

OUTDIR="/var/www/jenkins/badges/coverage/"

cnt=0
while [ $cnt -le 100 ]; do
	echo -n "Downloading "
	if [ $cnt -lt 50 ]; then
		echo "coverage-$cnt%-red.svg"
		wget -q https://img.shields.io/badge/coverage-$cnt%-red.svg -O ${OUTDIR}/coverage-$cnt%.svg
	elif [ $cnt -lt 75 ]; then
		echo "coverage-$cnt%-yellow.svg"
		wget -q https://img.shields.io/badge/coverage-$cnt%-yellow.svg -O ${OUTDIR}/coverage-$cnt%.svg
	else
		echo "coverage-$cnt%-green.svg"
		wget -q https://img.shields.io/badge/coverage-$cnt%-green.svg -O ${OUTDIR}/coverage-$cnt%.svg
	fi
	let cnt=cnt+1
done

chmod 644 ${OUTDIR}/coverage-*.svg

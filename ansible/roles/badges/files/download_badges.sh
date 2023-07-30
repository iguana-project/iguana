#!/bin/bash
: '
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin, Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under BSD-2-Clause License.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
   2. Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer
      in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
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

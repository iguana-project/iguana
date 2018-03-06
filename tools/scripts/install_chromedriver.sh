#!/bin/sh
: '
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
'
# instal script for the chrome webdriver

# import virtualenv directory
source $(dirname $0)/check_virtualenv_dir $@

if [ $(uname -s) = Darwin ]; then
    LINKSRC=chromedriver-Darwin
else
    # must be linux cause uname does not work on Windows
    if [ $(uname -m) = i686 ]; then
    	LINKSRC=chromedriver-Linux32
    else
    	LINKSRC=chromedriver-Linux64
    fi
fi

# activate virtualenv
# source $VIRTUALENV_DIR/bin/activate

# install the chromedriver // we did that alreay via refresh-reqs target in Makefile
# pip install chromedriver

# create the link
ln -sf ../src/chromedriver/chromedriver/bin/${LINKSRC} ${VIRTUALENV_DIR}/bin/chromedriver

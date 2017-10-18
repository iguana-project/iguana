#!/bin/sh
: '
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
'
# installation script for the firefox webdriver (geckodriver)

# import virtualenv directory
source $(dirname $0)/check_virtualenv_dir $@

# get the latest releases of the geckodriver
GECKODRIVER_RELEASES=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest | grep "browser_download_url" | sed -e 's/.*"browser_download_url": //' | sed -e 's:"::g')

# check which driver to use
if [ $(uname -s) = Darwin ]; then
    OS=macos
else
    # must be linux cause uname does not work on Windows
    if [ $(uname -m) = i686 ]; then
    	OS=linux32
    else
    	OS=linux64
    fi
fi

# select the url for the OS
DRIVER_URL=
for link in ${GECKODRIVER_RELEASES[@]}; do
    case "$link" in
      *$OS*)
        DRIVER_URL=$link
        ;;
    esac
done
# if something went wrong inform the user about it
if [ -z "$DRIVER_URL" ]; then
    echo "Couldn't find a suitable Geckodriver release."
    echo "Please download it manually from: https://github.com/mozilla/geckodriver/releases"
    echo "and copy it into $VIRTUALENV_DIR/bin/"
    exit 0
fi

# download the file
DIRVER_ARCHIVE=geckodriver.tar.gz
curl -L $DRIVER_URL -o $VIRTUALENV_DIR/$DIRVER_ARCHIVE

# untar it
DRIVER_FILE=geckodriver
tar -C $VIRTUALENV_DIR -zxf $VIRTUALENV_DIR/$DIRVER_ARCHIVE $DRIVER_FILE
rm -f $VIRTUALENV_DIR/$DIRVER_ARCHIVE

# create the link
ln -sf ../$DRIVER_FILE $VIRTUALENV_DIR/bin/$DRIVER_FILE

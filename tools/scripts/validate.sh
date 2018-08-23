#!/bin/bash
: '
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
'

# This script downloads all html from localhost:8000 and then validates it,
# using html5validator (vnu.jar). The validator needs Java8. You can set
# login credentials with the environment variables USER(=admin) and
# PASS(=passpass). Make sure your local webserver is running.
#
# The -f option filters out third party violations.
#
# Example usage:
#     make run &
#     USER=yodalf PASS="you shall not" validate.sh


username="admin"
[ -n "$USER" ] && username="$USER"
password="passpass"
[ -n "$PASS" ] && password="$PASS"
hostname="localhost"
host="${hostname}:8000"
vnu_version="18.7.23"


echo "Checking for validator (vnu.jar)..."
if [ ! -e tools/bin/vnu.jar ]
then
	echo "Downloading validator..."
	wget --quiet https://github.com/validator/validator/releases/download/$vnu_version/vnu.jar_$vnu_version.zip
	unzip -qq vnu.jar_$vnu_version.zip
	rm vnu.jar_*.zip
	mkdir -p tools/bin
	mv dist/vnu.jar tools/bin/
	rm -r dist
fi


echo "Preparing validation directory..."
mkdir validation -p
cd validation
rm -r ./*


# Login (csrf protection makes this a bit harder)
echo "Logging in..."
wget --quiet \
	--save-cookies cookies.txt \
	--keep-session-cookies \
	-O login_page \
	"$host/login"
token=$(grep -oP "(?<='csrfmiddlewaretoken' value=').*(?=' />)" login_page)
rm login_page

wget --quiet \
	--load-cookies cookies.txt \
	--keep-session-cookies \
	--save-cookies cookies.txt \
	--post-data="username=$username&password=$password&csrfmiddlewaretoken=$token" \
	"$host/login"

if grep -q "username and password" login
then
	echo "Login failed"
	rm login
	rm cookies.txt
	exit 1
fi
rm login


# Download the entire site
echo "Downloading all html..."
wget --quiet \
	--load-cookies cookies.txt \
	--keep-session-cookies \
	--recursive \
	--no-host-directories \
	--html-extension \
	--domains "$hostname" \
	--exclude-directories logout,static \
	--reject-regex "(.*)\?(.*)" \
	"$host"
rm cookies.txt

echo "Validating..."
if [ "$1" == "-f" ]
then
	java -jar ../tools/bin/vnu.jar --errors-only --skip-non-html --root . |& grep -v \
		-e 'The first child ' -e 'editsprint' -e 'id_file' -e 'due_date' -e 'created_at'
else
	java -jar ../tools/bin/vnu.jar --errors-only --skip-non-html --root .
fi

#!/bin/bash


# this script copies the following header into all source files if it doesn't exist there yet
: '
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin, Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under BSD-2-Clause License.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'

# This text is inserted into all html, scss, py files (__init__.py) excluded and into the logo.svg. If you want to overwrite the previous license-text you can use the "1" or "y" flag to do so. There is no need to insert this text into any css-files, since the only bigger one is the style.scss file from which style.css is generated.
# NOTE: empty files are skipped anyway




# Those are for pattern matching to be able to replace those license text without any extra effort and they should never be modified neither here nor in the license text otherwise this will produce problems during the replacement process.
LICENSE_START_0_HTML="<!--"
LICENSE_START_0_PY='"""'
LICENSE_START_0_SH=": '"
LICENSE_START_0_SCSS='/*'
LICENSE_START_0_SCSS_ESCAPED="\/\*"
LICENSE_START_1_ALL="Iguana"
LICENSE_END_HTML="-->"
LICENSE_END_PY='"""'
LICENSE_END_SH="'"
LICENSE_END_SCSS="\*\/"

LICENSE_TEXT="Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin, Michael Gunselmann, Katrin Raab, Christian Strate\n\nIguana is licensed under BSD-2-Clause License.\n\nRedistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:\n\n\t1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.\n\t2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.\n\nTHIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."

TEMP="\r${LICENSE_TEXT//\\n/\\r}\r"
# the same text as LICENSE_TEXT but with \r instead of \n because vim needs \r in write mode for a newline and slashes are escaped with prepending backslashes
LICENSE_TEXT_REPLACE="${TEMP//\//\\/}"
LICENSE_TEXT_HTML="<!--\n$LICENSE_TEXT\n-->"
# use \r instead of \n here! Otherwise it will break
LICENSE_TEXT_HTML_REPLACE="<!--$LICENSE_TEXT_REPLACE-->"
LICENSE_TEXT_PY="\"\"\"\n$LICENSE_TEXT\n\"\"\""
# use \r instead of \n here! Otherwise it will break
LICENSE_TEXT_PY_REPLACE="\"\"\"$LICENSE_TEXT_REPLACE\"\"\""
LICENSE_TEXT_SH=": '\n$LICENSE_TEXT\n'"
# use \r instead of \n here! Otherwise it will break
LICENSE_TEXT_SH_REPLACE=": '$LICENSE_TEXT_REPLACE'"
# use \r instead of \n here! Otherwise it will break
LICENSE_TEXT_SCSS="\/\*\n$LICENSE_TEXT\n\*\/"
LICENSE_TEXT_SCSS_REPLACE="\/\*$LICENSE_TEXT_REPLACE\*\/"


usage(){
	echo -e >&2 "Usage:\n\t$0 [{y,1,n,0}]\n\twhere y and 1 force an overwrite and n and 0 don't. Per default no overwrite takes places."
	exit 1
}

is_license_present(){
	file_type=$3
	# start and end contain the return values
	local -n start_l=$2
	line_number=1
	first_match=0
	# TODO this shall be faster with awk instead of a line by line read
	while IFS='' read -r line || [[ -n $line ]]; do
		# check whether LICENSE_START_0_<TYPE> is followed by a LICENSE_START_1_ALL
		if [ $first_match == 1 ]; then
			if [[ "$line" == *"$LICENSE_START_1_ALL"* ]]; then
				((start_l=$line_number-1))
				return
			else
				first_match=0
			fi
		fi
		if [[ $file_type == "html" ]]; then
			if [[ "$line" == *"$LICENSE_START_0_HTML"* ]]; then
				first_match=1
			fi
		elif  [[ $file_type == "py" ]]; then
			if [[ "$line" == *"$LICENSE_START_0_PY"* ]]; then
				first_match=1
			fi
		elif  [[ $file_type == "scss" ]]; then
			if [[ "$line" == *"$LICENSE_START_0_SCSS"* ]]; then
				first_match=1
			fi
		elif  [[ $file_type == "sh" ]]; then
			if [[ "$line" == *"$LICENSE_START_0_SH"* ]]; then
				first_match=1
			fi
		else
			echo "UNSUPPORTED TYPE"
		fi
		((line_number+=1));
	done < $1
	start_l=0
}



if  [ -n "$1" ] && [ "$1" != "1" ] && [ "$1" != "y" ] && [ "$1" != "0" ] && [ "$1" != "n" ]; then
	usage
fi
if [ -n "$1" ] && ([ "$1" == "1" ] || [ "$1" == "y" ]); then
	overwrite=true
	echo "Note: overwrite mode is active this might take some time because we spawn many vim-instances. :/"
fi

# header for html-files
for file in `find . -name "*.html"`; do
	# skip olea_tooltip.html, because there is no neat way to hide this comment within the tooltip itself
	if [[ "$file" == *"olea_tooltip.html"* ]]; then
		continue
	fi
	is_license_present $file start_line_of_license "html"
	if [ "$start_line_of_license" != 0 ]; then
		# NOTE: don't set overwrite to false at initialisation - this is bash!
		if [ $overwrite ]; then
			# unfortunately it doesn't seems like there is a non-greedy replace in sed, so we use the vim-version to do the trick for us
			ex -n +"${start_line_of_license},s/$LICENSE_START_0_HTML\n$LICENSE_START_1_ALL\(.*\n*\)\{-\}$LICENSE_END_HTML/$LICENSE_TEXT_HTML_REPLACE/" -cx $file
		fi
	else
		sed -i "1i$LICENSE_TEXT_HTML" $file
	fi
done

# header for python files
for file in `find . -name "*.py"`; do
	# exclude __init__.py and any migrations-files
	if [ "${file##*/}" == "__init__.py" ] || [[ "$file" == *"migrations"* ]] ; then
		continue
	fi
	is_license_present $file start_line_of_license "py"
	if [ "$start_line_of_license" != 0 ]; then
		# NOTE: don't set overwrite to false at initialisation - this is bash!
		if [ $overwrite ]; then
			# unfortunately it doesn't seems like there is a non-greedy replace in sed, so we use the vim-version to do the trick for us
			ex -n +"${start_line_of_license},s/$LICENSE_START_0_PY\n$LICENSE_START_1_ALL\(.*\n*\)\{-\}$LICENSE_END_PY/$LICENSE_TEXT_PY_REPLACE/" -cx $file
		fi
	else
		# this is the only file with a shebang and hence the comment should start in the second line instead of the first one
		if [ "${file##*/}" == "manage.py" ]; then
			sed -i "2i$LICENSE_TEXT_PY" $file
		else
			sed -i "1i$LICENSE_TEXT_PY" $file
		fi
	fi
done

# header for bash files
for file in `find .. -name "*.sh"`; do
	is_license_present $file start_line_of_license "sh"
	if [ "$start_line_of_license" != 0 ]; then
		# NOTE: don't set overwrite to false at initialisation - this is bash!
		if [ $overwrite ]; then
			# unfortunately it doesn't seems like there is a non-greedy replace in sed, so we use the vim-version to do the trick for us
			ex -n +"${start_line_of_license},s/$LICENSE_START_0_SH\n$LICENSE_START_1_ALL\(.*\n*\)\{-\}$LICENSE_END_SH/$LICENSE_TEXT_SH_REPLACE/" -cx $file
		fi
	else
		# these are files with a shebang and hence the comment should start in the second line instead of the first one
		sed -i "2i$LICENSE_TEXT_SH" $file
	fi
done

# header for scss-files - ignore non-iguana scss files
for file in `find common/scss/iguana -name "*.scss"`; do
	is_license_present $file start_line_of_license "scss"
	if [ "$start_line_of_license" != 0 ]; then
		# NOTE: don't set overwrite to false at initialisation - this is bash!
		if [ $overwrite ]; then
			# unfortunately it doesn't seems like there is a non-greedy replace in sed, so we use the vim-version to do the trick for us
			ex -n +"1,s/$LICENSE_START_0_SCSS_ESCAPED\n$LICENSE_START_1_ALL\(.*\n*\)\{-\}$LICENSE_END_SCSS/${LICENSE_TEXT_SCSS_REPLACE}/" -cx $file
		fi
	else
		sed -i "1i$LICENSE_TEXT_SCSS" $file
	fi
done



# header for js-files
# those are the js-files we wrote by our own
js_files=("draw_activity_heatmap.js" "draw_last_seven.js" "filter-issues.js" "draw_bars_project_detail.js" "draw_spark.js")
for file_name in ${js_files[@]}; do
	file="common/static/js/$file_name"
	# we use the scss-tag here because the syntax for comments is equivalent to scss ones
	is_license_present $file start_line_of_license "scss"
	if [ "$start_line_of_license" != 0 ]; then
		# NOTE: don't set overwrite to false at initialisation - this is bash!
		if [ $overwrite ]; then
			# unfortunately it doesn't seems like there is a non-greedy replace in sed, so we use the vim-version to do the trick for us
			ex -n +"1,s/$LICENSE_START_0_SCSS_ESCAPED\n$LICENSE_START_1_ALL\(.*\n*\)\{-\}$LICENSE_END_SCSS/${LICENSE_TEXT_SCSS_REPLACE}/" -cx $file
		fi
	else
		sed -i "1i$LICENSE_TEXT_SCSS" $file
	fi
done

# logo.svg
file="common/static/css/logo.svg"
is_license_present $file start_line_of_license "html"
if [ "$start_line_of_license" != 0 ]; then
	# NOTE: don't set overwrite to false at initialisation - this is bash!
	if [ $overwrite ]; then
		# unfortunately it doesn't seems like there is a non-greedy replace in sed, so we use the vim-version to do the trick for us
		ex -n +"${start_line_of_license},s/$LICENSE_START_0_HTML\n$LICENSE_START_1_ALL\(.*\n*\)\{-\}$LICENSE_END_HTML/$LICENSE_TEXT_HTML_REPLACE/" -cx $file
	fi
else
	# insert in line 2 because the comment has to be within the xml-tag.
	sed -i "2i$LICENSE_TEXT_HTML" $file
fi

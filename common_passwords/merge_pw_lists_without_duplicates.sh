#!/bin/bash
: '
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
'

huge_list=huge_list
tmp_file=tmp_file
tmp_file2=tmp_file2

usage(){
	echo -e >&2 "Usage:\n\t$0 <wordlist_0> [<wordlist_1>][<wordlist_2>][<wordlist_3>][...]\nThis tool merges all lists into one, sorts them and removes duplicates. The result is stored in $huge_list."
	exit 1
}

if [ -z "$1" ];then
	usage
fi

echo -e "Warning, $huge_list will be deleted if it already exists, are you sure you want to \e[34mcontinue\e[0m? If so please enter \e[34my\e[0m, otherwise the script will exit."
read input
if [ "$input" != "y" ]; then
	echo -e "\e[31mAborting!\e[0m"
	exit 1
fi


# cat all words
rm -f $huge_list
for file in "$@"; do
	cat $file >> $huge_list
done

# remove duplicates
awk '!seen[$0]++' $huge_list > $tmp_file

# remove lines with less than 8 number of chars and sort them
sed -r '/^.{,7}$/d' $tmp_file > $tmp_file2
sort $tmp_file2 > $huge_list

rm -f $tmp_file
rm -f $tmp_file2

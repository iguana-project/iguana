#!/bin/bash
: '
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
'

pushd $TRAVIS_BUILD_DIR/ansible

tag=$(git tag -l production-* | sort -V | tail -n1)

touch last_deployed_tag
if [ "$tag" != "$(<last_deployed_tag)" ]
then
	echo "Deploying $tag to production"
	echo $tag > last_deployed_tag

	export ANSIBLE_HOST_KEY_CHECKING=False
	ansible-playbook -i hosts deploy_production.yml --extra-vars "git_checkout_version=$tag"
fi

popd

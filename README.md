# Iguana
[![Coverage Status](https://img.shields.io/coveralls/github/iguana-project/iguana/master.svg)](https://coveralls.io/github/iguana-project/iguana?branch=master)
[![Test & Build](https://github.com/iguana-project/iguana/actions/workflows/test_and_build.yml/badge.svg)](https://github.com/iguana-project/iguana/actions/workflows/test_and_build.yml)
![Django 2.2 support](https://img.shields.io/badge/django-v2.2-blue)
![Python >=3.7 required](https://img.shields.io/badge/python-v3.7|3.8|3.9|3.10-blue)

## Description
Iguana is a mixture of a ticket system, an issue tracker and an issue management system, heavily based on basic functions being easy to use. So Iguana can help you to plan the next schedule and have always a nice overview about your current tasks depending on your needs, especially for working in groups. There is a kanban board to keep an eye on the progress until the end of the next planning stage and also a backlog to have the ability for scheduling of long-terms. In combination with a mechanism to log time spent on different tasks individually those are the essential functionalities.

For more detailed documentation including a list of features see our github documentation page at https://iguana-project.github.io.

### Features
* [Sprintboard](https://iguana-project.github.io/index.html#sprintboard)<br />
	Provides possibility for short-term scheduling.
* [Backlog](https://iguana-project.github.io/index.html#backlog)<br />
	Provides possibility for long-term scheduling.
* [Olea-bar](https://iguana-project.github.io/#olea-bar)<br />
	A command line tool to create and edit existing issues.
* [Time-logging](https://iguana-project.github.io/#time-logging)<br />
	For both issues and projects, where the value for the later one is simply the sum of relative issue-time-logs.
* Activity charts<br />
	To keep an eye on the progress of a specific project in both aspects, for time management and amount of activities (e.g. commits). There is an [acitivty overview](https://iguana-project.github.io/demonstration/activity.html#demo-activity_overview) for a project and a [different chart](https://iguana-project.github.io/demonstration/time_logging.html#demo-chart) for the proportion of issues on a single project.
* [Notifications](https://iguana-project.github.io/demonstration/activity.html#navigation)<br />
	Present multiple ways to notify you for different events. In the future it will be customizable which notifications shall be shown with which feature.
  * [Activity stream](https://iguana-project.github.io/#activity_stream)<br />
	show the latest actions in multiple streams.
  * [Discussion App](https://iguana-project.github.io/demonstration/activity.html#demo-discussion_app)<br />
	Get notifications on changes or comments on a specific issue you set a watchpoint for.
  * [Email notifications](https://iguana-project.github.io/demonstration/activity.html#demo-discussion_app)<br />
	Sends notifications via email.
* [Search function](https://iguana-project.github.io/demonstration/search_function.html#navigation)<br />
	Search any type of a specific data with regex support.
* [Integrations](https://iguana-project.github.io/index.html#integrations)<br />
	To simplify your workflow
  * Git
  * Slack
* [REST-API](https://iguana-project.github.io/#rest-api)<br />
	To extend your possibilities on how to use iguana.
* [Markdown support](https://iguana-project.github.io/#markdown_support)<br />
	For nicer formatting of comments and descriptions.
* [Ansible](#using-ansible-for-deployment)<br />
	Easy and fast start due to the usage of ansible
* [Docker](#docker)<br />
	Alternatively an even easier and faster start with Docker



## Installation
### Manual

#### Preperation

If you want to manually install Iguana, there are some dependencies and actions that must be installed and done before:

##### Dependencies
**TODO**: more dependencies required

We generally try to avoid any non-python dependencies but this doesn't always work well. The test cases need the Exempi library so for the [development environment](README.md#Development) this is required and can be installed like [this](https://python-xmp-toolkit.readthedocs.io/en/latest/installation.html#exempi):

```bash
apt-get install libexempi3  # Ubuntu/Debian
pacman -S exempi		    # Arch Linux
brew install exempi         # OS X
```

##### Setup Python Version

Iguana is currently tested against **Python 3.7**.</br>
It may be also run on higher versions. But if you run into any problems, please test first if they also occour with Python 3.7.

To install Python 3.7 locally (independent from your current system version), you can use [pyenv](https://github.com/pyenv/pyenv). For installation and setting up *pyenv* please stick to their documentation: https://github.com/pyenv/pyenv/wiki

Once you've got *pyenv* running execute the following command in the main iguana directory:

```bash
pyenv install -v $(cat .python-version)
```

If everything is correctly setup and if you simply run `python` in your command shell, the python interpreter with the version specified in the `.python-version` file should be started.

**Common problems using *pyenv*:** Since *pyenv* is compiling every python version other than your system one direct on your PC, it can happen that after some time this version won't work any more. Often there are errors of missing shared libraries or something like that, when you try to start Iguana or the Python interpreter installed by *pyenv*. This can happen e.g. after a system update/upgrade. To solve this issue simply reinstall the Python version with the abovev *pyenv* command.

#### Production
To setup Iguana in a production environment you simply have to call:

```bash
make production
```

This command runs the following Makefile targets:

  * `setup-virtualenv`
  * `django makemigrations`
  * `django migrate`
  * `css`

#### Staging
To setup Iguana in a staging environment you simply have to call:

```bash
make staging
```

This does the same as the production target but it creates the staging virtual environment.

#### Development
To setup Iguana in a development you simply have to call:

```bash
make development ++webdriver [<webdriver>]
```

The `<webdriver>` option the driver for the `setup-webriver` target can be specified ("chrome" is used as default). Beside that the following targets are executed:

* `production`
* `setup-webdriver <webdriver>`

#### Starting Iguana
Currently Iguana supports only [Nginx](https://nginx.org/en/) as web server backend. For configuring Nginx and using [Gunicorn](http://gunicorn.org/) together with Django please stick to the official documentation: https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/gunicorn/

#### Starting the local Iguana instance
To start the local Django web server simply run:

```bash
make run
```


### Docker
#### Build images
Three images can be built with the Dockerfile:

* **development** (default)

  `docker build -f Dockerfile .`
* **staging/production**

  `docker build -f Dockerfile . --build-arg VARIANT=[staging|production] [--build-arg USE_NGINX=[false|true]]`

  The `USE_NGINX` variable indicates if a (basic) Nginx server should be included in the image. The default value is `false`!

#### Start a container
Each Iguana docker image can be started with the following command:
```bash
docker exec -d \
	-p 80:8000 \
	-v <data_directory>:/files \
	-e TZ=<time zone> \
	-e PUID=<user ID> \
	-e PGID=<group ID> \
	<Iguana image ID>
```

| Environment variable | Default value | Description |
|-|-|-|
| TZ | UTC | Set the time zone for the container, e.g. Europe/Berlin |
| PUID | 1000 | The ID of the user running Iguana in the container |
| PGID | 1000 | The group ID of the above user |

But in staging/production environment more configuration should be done by the user! Therefore a [settings.json](files/settings.json) file is placed in the Docker volume after the first run. You can edit this file to your needs (see [Configuration section -> settings.json](README.md#settingsjson)). To apply the canges simply restart the container. Please look especially at the `SECRET_KEY` and `HOST/ALLOWED_HOSTS` settings!

If a Nginx server was included in the image (with `USE_NGINX=true`), the `nginx.conf` file can also be found on the Docker volume. But for real production environments, a separate Nginx container is recommended!

All files uploaded to Iguana are placed in the `media` directory on the Docker volume.

**TODO**: add DockerHub badges and links


### Using Ansible for deployment
**TODO:** write Ansible instructions


### Integrations
* **TODO:** write instructions for git integration
* **TODO:** write instructions for slack integration



## Makefile targets
These targets can be run with:

```bash
make <target> [++option]
```

**Note** that options have to begin with `+` or `++` instead of `-` or `--`. This is due to a bug that prevents passing options to make targets.

### Main:
* **help**<br />
Prints a short description for each Makefile target.

* **production**<br />
See subsection [Production](README.md#Production).

* **staging**<br />
See subsection [Staging](README.md#Staging).

* **development** `[+w <webdriver>]`<br />
See subsection [Development](README.md#Development).

### Django management:
* **django** `<command> [<args>]`<br />
Any command and its arguments gets directly passed to Django's `manage.py` script. Please have a look at the official Django documentation for a list of supported commands: https://docs.djangoproject.com/en/dev/ref/django-admin/

* **test** `[+a <appname>|+f|+c] [+i]`<br />
Run the Django unit tests. If an application name is provided with `+a`, only that app is tested. To run the functional tests use the `+f` option. If all tests should be run, use option `+c`. With the option `+i` the warnings and errors from imported packages get suppressed.

* **run**<br />
Run the default django server.

### Source code management:
* **setup-virtualenv**<br />
This target prepares the virtual python environment in which this project is executed. The packages for the virtual environment are defined in the file [production.req](requirements/production.req) or [development.req](requirements/development.req). This depends on which main target you have chosen before.

* **css**<br />
See section [Styling](README.md#Styling).

* **set-webdriver** `<webdriver>`<br />
This target configures the webdriver for the functional tests. You can replace `<webdriver>` with `chrome`, `firefox` or `safari`.

* **requirements**
    * **install**<br />
    Reinstall all packages in the virtual environment. Which packages are installed depend on what main target you have run in the initialization process.
    * **check**<br />
    Check whether the used requirements are up to date or not.

* **coverage** `[+a <appname>|+f|+c] {report,html,xml,erase}`<br />
Run the coverage tool on the Django tests. With argument `+a` anapp for which the coverage should be measured can be specified. `+f` measures the coverage for all funtional tests and `+c` performs a measurement across all tests. To get a better output you can run one of the following commands:
    * **report**<br />
    Get the coverage in text form.
    * **html**<br />
    Get the coverage as a html website.
    * **xml**<br />
    Get the coverage as a xml file.
    * **erase**<br />
    Delete the last coverage report.

* **list**
    * **bugs**<br />
    List all occurrence of the tag `TODO BUG`.
    * **missing_testcases**<br />
    List all occurrence of the tag `TODO TESTCASE`.

* **add-license**<br />
Insert the license header into all source files.

* **new-release**<br />
Tag the current commit as a production release.


### Styling
Currently the style is stored in [src/common/scss/iguana.scss](src/common/scss/iguana.scss). To build it run
`make css`. For Selenium tests use `StaticLiveServerTestcase` instead of
`LiveServerTestcase` to make sure static files (like css) are served.

Documentation on Sass and SCSS: [sass-lang guide](https://sass-lang.com/guide)

I propose we use SCSS, as it is a superset of CSS and the default Sass syntax.
If we change our mind, there are tools to convert between the two syntaxes.

### Translation
Please use translation hooks in templates (see [\_base.html](src/common/templates/_base.html) for an example)
and code (`ugettext` as `_`).

You can create/update the `*.po` in the locale directory by running `make django makemessages +l <lang-code>`. The default language is English (code: en). This file is where the actual translations go. It should be checked
in after updating. This uses the GNU gettext toolset.

For new translations to be usable by django, run `make django compilemessages`.

To see a page in a different language, open it with a different language prefix
in the url. For example `/de/login` instead of `/en/login`.


## Configuration
Iguana has a lot of settings that can be changed by the user. The settins files are stored in the [src/common/settings](src/common/settings) package. The package structure is:

```bash
common/settings
          |- __init__.py
          |- common.py
          |- global_conf.py
          |- local_conf.py
```


#### \_\_init\_\_.py
A default init-file gets created by the Makefile target **initialize-settings** (see section [Makefile targets](README.md#Makefile-targets)).<br />
For the development process this file can contain additional settings that should not be published in the repository. Mainly the Django-`SECRET_KEY = '...'` setting is defined here, when the project is in the development environment.<br />
**Important:** The file must start with the line:

```python
from <site_config> import *
```

You can replace `<site_config>` with (don't forget the '**.**'):
* `.local_conf`: the development settings are loaded
* `.global_conf`: the production and staging settings are loaded

#### common.py
This file contains the basic settings that are the same for the other two configuration files.<br />
**This file should not be changed by the user!** It contains basic settings for the Django framework. Changing these settings without knowing what you do could lead to unexpected behaviour.

#### global_conf.py
Basically this file contains all settings that are required to run Iguana in an staging or production environment.<br />
But the settings that should be changed by the user are loaded from the file [settings.json](files/settings.json). See section [settings.json](README.md#settingsjson).

#### local_conf.py
This file contains all settings that are required to run Iguana in a development environment.<br />
Normally there's no need to change these settings.

#### settings.json
**TODO**: describe settings.json


## Plan of the future
For short and long term plans see the [official documentation](https://iguana-project.github.io/#plans).

## Question and answers
For questions and answers please also stick to the [official documentation](https://iguana-project.github.io/#q_and_a). In case you have any other questions don't hesitate to hit us up.

## License
Iguana was mainly developed with the Django framework (https://www.djangoproject.com).


### Main license
**Iguana is licensed under the CC-BY-SA license:**
<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International License</a>. Since we use the version 4 of CC-BY-SA there is not necessarily an incompatibility with GPL - see <a href="https://creativecommons.org/faq/#can-i-apply-a-creative-commons-license-to-software">Can I apply a Creative Commons license to software?</a> and <a href="https://wiki.creativecommons.org/wiki/ShareAlike_compatibility:_GPLv3">ShareAlike compatibility: GPLv3</a>. If you see any problems that are caused by that CC-BY-SA license tell us and we might find a solution.

<!-- Header for all source files -->
<!-- Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>. -->


### Plug-in licenses
Besides the following plug-ins were used:

| Plug-in / Software | License |
| ------------------ | ------- |
| [bleach](https://github.com/mozilla/bleach) | [Apache License 2.0](https://github.com/mozilla/bleach/blob/master/LICENSE) |
| [celery](http://docs.celeryproject.org/en/latest/) | [BSD License](http://docs.celeryproject.org/en/latest/) |
| [chromedriver](https://github.com/enkidulan/chromedriver) | Apache License 2.0 |
| [coverage](https://coverage.readthedocs.io) | [Apache License 2.0](https://github.com/nedbat/coveragepy/blob/master/LICENSE.txt) |
| [Django](https://www.djangoproject.com) | [BSD License](https://github.com/django/django/blob/master/LICENSE) |
| [django-activity-stream](https://django-activity-stream.readthedocs.io) | [BSD License](https://github.com/justquick/django-activity-stream/blob/master/LICENSE.txt) |
| [django-autocomplete-light](https://django-autocomplete-light.readthedocs.io) | [MIT License](https://github.com/yourlabs/django-autocomplete-light/blob/master/LICENSE) |
| [django-bootstrap3](https://django-bootstrap3.readthedocs.io) | [Apache License 2.0](https://github.com/dyve/django-bootstrap3/blob/master/LICENSE) |
| [django-cuser](https://github.com/Alir3z4/django-cuser) | [BSD License](https://github.com/Alir3z4/django-cuser/blob/master/LICENSE) |
| [django-bootstrap-datepicker-plus](https://github.com/monim67/django-bootstrap-datepicker-plus) | [Apache License 2.0](https://github.com/monim67/django-bootstrap-datepicker-plus/blob/master/LICENSE) |
| [django-extensions](https://github.com/django-extensions/django-extensions) | [MIT License](https://github.com/django-extensions/django-extensions/blob/master/LICENSE)
| [django-filter](https://github.com/carltongibson/django-filter) | [BSD License](https://github.com/carltongibson/django-filter/blob/develop/LICENSE) |
| [django-pagedown](https://github.com/timmyomahony/django-pagedown) | [BSD License](https://github.com/timmyomahony/django-pagedown/blob/master/LICENSE.txt) |
| [django-redis](https://github.com/niwinz/django-redis) | [BSD License](https://github.com/niwinz/django-redis/blob/master/LICENSE) |
| [djangorestframework](https://github.com/encode/django-rest-framework) | [BSD License](https://github.com/encode/django-rest-framework/blob/master/LICENSE.md) |
| [djangorestframework-simplejwt](https://github.com/davesque/django-rest-framework-simplejwt) | [MIT License](https://github.com/davesque/django-rest-framework-simplejwt/blob/master/LICENSE.txt) |
| [django-sendfile](https://github.com/johnsensible/django-sendfile) | [BSD License](https://github.com/johnsensible/django-sendfile/blob/master/LICENSE) |
| [django-simple-captcha](https://github.com/mbi/django-simple-captcha) | [MIT License](https://github.com/mbi/django-simple-captcha/blob/master/LICENSE) |
| [django-test-without-migrations](https://github.com/henriquebastos/django-test-without-migrations/) | [MIT License](https://github.com/henriquebastos/django-test-without-migrations/blob/master/LICENSE) |
| [GitPython](https://gitpython.readthedocs.io) | [BSD License](https://github.com/gitpython-developers/GitPython/blob/master/LICENSE) |
| [gunicorn](https://gunicorn.org) | [MIT License](https://github.com/benoitc/gunicorn/blob/master/LICENSE) |
| [markdown](https://pythonhosted.org/Markdown/) | [BSD License](https://github.com/waylan/Python-Markdown/blob/master/LICENSE.md) |
| [markdown-urlize](https://github.com/r0wb0t/markdown-urlize) | [BSD License](https://github.com/r0wb0t/markdown-urlize/blob/master/LICENSE) |
| [model-mommy](https://model-mommy.readthedocs.org) | [Apache License 2.0](https://github.com/vandersonmota/model_mommy/blob/master/LICENSE) |
| [Pillow](https://python-pillow.org) | [PIL Software License](https://github.com/python-pillow/Pillow/blob/master/LICENSE) |
| [piprot](https://github.com/sesh/piprot) | [MIT License](https://github.com/sesh/piprot/blob/master/LICENCE.txt) |
| [Piexif](https://github.com/hMatoba/Piexif) | [MIT License](https://github.com/hMatoba/Piexif/blob/master/LICENSE.txt) |
| [ply](http://www.dabeaz.com/ply/) | BSD License |
| [psycopg2](http://initd.org/psycopg/) | [GNU LGPL v3.0](https://github.com/psycopg/psycopg2/blob/master/LICENSE) |
| [pycodestyle](https://github.com/PyCQA/pycodestyle) | [Expat License](https://github.com/PyCQA/pycodestyle/blob/master/LICENSE) |
| [python-dateutil](https://github.com/dateutil/dateutil/) | [BSD License](https://github.com/dateutil/dateutil/blob/master/LICENSE) |
| [python-magic](https://github.com/ahupp/python-magic) | [MIT license](https://github.com/dateutil/dateutil/blob/master/LICENSE) |
| [python-xmp-toolkit](https://github.com/python-xmp-toolkit/python-xmp-toolkit) | [ESA/ESO and CRS4 license](https://github.com/python-xmp-toolkit/python-xmp-toolkit/blob/master/LICENSE) |
| [pytz](https://github.com/stub42/pytz) | [MIT license](http://pythonhosted.org/pytz/#license) |
| [redis](https://github.com/antirez/redis) | [BSD License](https://github.com/antirez/redis/blob/unstable/COPYING) |
| [requests](http://docs.python-requests.org) | [Apache License 2.0](https://github.com/kennethreitz/requests/blob/master/LICENSE) |
| [selenium](http://www.seleniumhq.org) | [Apache License 2.0](https://github.com/SeleniumHQ/selenium/blob/master/LICENSE)
| [sendgrid-django](https://github.com/elbuo8/sendgrid-django) | [MIT License](https://github.com/elbuo8/sendgrid-django/blob/master/LICENSE) |
| [slackclient](https://github.com/slackapi/python-slackclient) | [MIT License](https://github.com/slackapi/python-slackclient/blob/master/LICENSE) |

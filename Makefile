###########
# Variables
###########

# global variables
SHELL = /bin/bash
BASE = $(shell pwd)

# virtualenv settings
VIRTUALENV_BASE = $(BASE)/virtualenv
export PATH := $(VIRTUALENV_BASE)/bin:$(PATH))
# the -bb "-b Issue warnings about str(bytes_instance), str(bytearray_instance) and comparing bytes/bytearray  with str. (-bb: issue errors)"
# s.a. https://docs.djangoproject.com/en/2.0/releases/2.0/#removed-support-for-bytestrings-in-some-places
PYTHON = $(VIRTUALENV_BASE)/bin/python -bb
COVERAGE = $(VIRTUALENV_BASE)/bin/coverage

# django settings
DJANGO_BASE = $(BASE)/src
DJANGO_SETTINGS = common.settings
DJANGO_STATIC = $(DJANGO_BASE)/common/static
DJANGO_SCSS = $(DJANGO_BASE)/common/scss
DJANGO_SETTINGS_FILE = $(DJANGO_BASE)/common/settings/__init__.py
WEBDRIVER_CONF = $(DJANGO_BASE)/common/settings/webdriver.py
# relative to DJANGO_BASE
DJANGO_MANAGE = manage.py

# tools directory
TOOLS = $(BASE)/tools
SCRIPTS = $(TOOLS)/scripts

# git hooks directory
GITHOOKS = $(BASE)/.git/hooks

# available web drivers
WEBDRIVERS = chrome firefox safari


#######################
# No changes from here!
#######################

# hack for making make silent (gives better output when specifying a django app as target)
MAKEFLAGS += -s

# custom git hooks (relative to the BASE path)
CUSTOM_GIT_HOOKS = $(shell find $(TOOLS)/git-hooks -type f -not -path '*/\.*' | sed -n 's|^$(BASE)/|./|p')

# get all apps from the django installation
ifneq ("$(wildcard $(VIRTUALENV_BASE))","")
DJANGO_INSTALLED_APPS = $(shell $(PYTHON) $(SCRIPTS)/getInstalledDjangoApps.py $(DJANGO_BASE))
DJANGO_INSTALLED_APPS_WILDCARD = $(foreach app,$(DJANGO_INSTALLED_APPS),$(app).%)
endif

# get all .scss files
SCSS_FILES = $(shell find $(DJANGO_SCSS) -type f -name "*.scss" -not -path '*/\.*' -exec basename {} .scss \;)

# get all migrations folders
MIGRATION_FOLDERS = $(shell find $(DJANGO_BASE) -type d -name "migrations" -not -path '*/\.*')

# look for perl executable
PERL = $(shell command -v perl 2> /dev/null)
# colors for the inline perl script below
GREEN = $(shell tput -Txterm setaf 2)
WHITE = $(shell tput -Txterm setaf 7)
YELLOW = $(shell tput -Txterm setaf 3)
RESET = $(shell tput -Txterm sgr0)
# inline perl script for displaying help texts
HELP_FUN = \
    %help; \
    while(<>) { push @{$$help{$$2 // 'other'}}, [$$1, $$3] if /^([a-zA-Z\-\_]+)\s*:.*\#\#(?:@([a-zA-Z\-]+))?\s(.*)$$/ }; \
    print "usage: make [target]\n\n"; \
    for (sort keys %help) { \
    print "${WHITE}$$_:${RESET}\n"; \
    for (@{$$help{$$_}}) { \
    $$sep = " " x (25 - length $$_->[0]); \
    print "  ${YELLOW}$$_->[0]${RESET}$$sep${GREEN}$$_->[1]${RESET}\n"; \
    }; \
    print "\n"; }

# settings file for the Makefile
MAKE_SETTINGS_FILE = $(BASE)/.makeSettings


#########
# Targets
#########

# XXX Don't forget to update the phony targets as soon as the makefile is extended
# phony targets
.PHONY: default help $(DJANGO_INSTALLED_APPS) $(DJANGO_INSTALLED_APPS_WILDCARD) $(WEBDRIVERS) production staging development setup-webdriver check-webdriver setup-virtualenv refresh-reqs initialize-settings link-git-hooks run startapp makemigrations migrate test test-ign_imp_errs func_tests messages compilemessages coverage coverage_func coverage-report coverage-html coverage-xml coverage-erase css remove-dev_stage-setting check-dev_staging save-dev_stage-setting make-messages compile-messages list_bugs list_missing_testcases add_license_header check_requirements

# default target
default: production
production: ##@main Configure everything to be ready for production.
production: remove-dev_stage-setting setup-virtualenv initialize-settings css

# remove the saved development or staging state
remove-dev_stage-setting:
	@$(if $(wildcard $(MAKE_SETTINGS_FILE)),\
		rm $(MAKE_SETTINGS_FILE),)

help: ## Show this help.
ifdef PERL
	@perl -e '$(HELP_FUN)' $(MAKEFILE_LIST)
else
	@IFS=$$'\n' ; \
	printf "usage: make [target]\n\n"; \
	help_lines=(`fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##/:/' | sort`); \
	printf "%-25s %s\n" "target" "help" ; \
	printf "%-25s %s\n" "------" "----" ; \
	for help_line in $${help_lines[@]}; do \
		IFS=$$':' ; \
		help_split=($$help_line) ; \
		if [ -z "$$help_split" ]; then \
			continue; \
		fi; \
		help_command=`echo $${help_split[0]} | sed -e 's/^ *//' -e 's/ *$$//'` ; \
		help_info=`echo $${help_split[2]} | sed -e 's/^ *//' -e 's/ *$$//' | sed -e 's/^@[^ ]* //'` ; \
		printf "$(YELLOW)"; \
		printf "%-25s %s" $$help_command ; \
		printf "$(GREEN)"; \
		printf "%s" $$help_info; \
		printf "$(RESET)\n"; \
	done
endif

# make a target for each django app
$(DJANGO_INSTALLED_APPS):
	@# set the global APPNAME variable
	@$(eval APPNAME := $@)
$(DJANGO_INSTALLED_APPS_WILDCARD):
	@$(eval APPNAME := $@)

# make a target for each webdriver
$(WEBDRIVERS):
	@# set the global WEBDRIVER variable
	@$(eval WEBDRIVER := $@)

# prepare everything for the development process
development: ##@development Configure everything to be ready for development.
development: DEVELOPMENT = true
development: production link-git-hooks setup-webdriver migrate save-dev_stage-setting

# prepare everything for the staging environment
staging: ##@main Configure everything to be ready for a staging.
staging: STAGING = true
staging: production save-dev_stage-setting

# setup the webdriver
setup-webdriver: ##@development <drivername> Install the specified webdriver.
setup-webdriver: check-webdriver
	@echo "# This file is automatically generated by the Makefile." > $(WEBDRIVER_CONF); \
	echo "# Do not manually edit it!" >> $(WEBDRIVER_CONF); \
	echo >> $(WEBDRIVER_CONF); \
	echo "WEBDRIVER = \"$(WEBDRIVER)\"" >> $(WEBDRIVER_CONF); \
	if [ -f "$(SCRIPTS)/install_$(WEBDRIVER)driver.sh" ]; then \
		$(SHELL) $(SCRIPTS)/install_$(WEBDRIVER)driver.sh $(VIRTUALENV_BASE); \
	fi

check-webdriver: $(filter $(WEBDRIVERS),$(MAKECMDGOALS))
	@# check if already a webdriver config is present
	@# if not, use default chrome driver; else use the already defined value
	@$(if $(WEBDRIVER),,\
		@$(if $(wildcard $(WEBDRIVER_CONF)),\
			$(eval WEBDRIVER := $(shell grep "WEBDRIVER =" $(WEBDRIVER_CONF) | grep -o '".*"' |sed 's/"//g')) \
			,\
			echo "Default webdriver 'chrome' is used" \
			$(eval WEBDRIVER := chrome)))

# setup a virtualenv environment for django
setup-virtualenv: ##@main Setup the virtual environment for django. Add "dev" to create the development environment. Add "stage" to create the staging environment.
setup-virtualenv: check-dev_staging
ifneq ("$(wildcard $(VIRTUALENV_BASE))","")
	@echo "WARNING: The virtual environment is already set up."
	@# call refresh-reqs
	@$(if $(filter $(DEVELOPMENT),true),\
		@$(MAKE) refresh-reqs dev,\
		@$(if $(filter $(STAGING),true),\
			@$(MAKE) refresh-reqs stage,\
			@$(MAKE) refresh-reqs))
else
	@# check for development
	@$(if $(filter $(DEVELOPMENT),true),\
		source $(SCRIPTS)/activate $(VIRTUALENV_BASE) --development,\
		@$(if $(filter $(STAGING),true),\
			source $(SCRIPTS)/activate $(VIRTUALENV_BASE) --staging,\
			source $(SCRIPTS)/activate $(VIRTUALENV_BASE)))
endif

# reinstall all pip requirements
refresh-reqs: ##@main Reinstall all requirements. Add "dev" to install the development requirements. Add "stage" to install the staging requirements.
refresh-reqs: check-dev_staging
	@$(if $(filter $(DEVELOPMENT),true),\
		source $(SCRIPTS)/activate $(VIRTUALENV_BASE) --refresh --development,\
		@$(if $(filter $(STAGING),true),\
			source $(SCRIPTS)/activate $(VIRTUALENV_BASE) --refresh --staging,\
			source $(SCRIPTS)/activate $(VIRTUALENV_BASE) --refresh))

# generate a SECRET_KEY for django and save it in the settings module
initialize-settings: ##@main Generate a SECRET_KEY for django. Add "dev" to use the development settings.
initialize-settings: check-dev_staging
	@# create the settings file
	@$(if $(filter $(DEVELOPMENT),true),\
		echo "from .local_conf import *" > $(DJANGO_SETTINGS_FILE), \
		echo "from .global_conf import *" > $(DJANGO_SETTINGS_FILE))

	@# generate a SECRET_KEY only for developing
	@# for staging and production a separate secrets file should be used
	@$(if $(filter $(DEVELOPMENT),true),\
		echo >> $(DJANGO_SETTINGS_FILE);\
		echo -n "SECRET_KEY = '" >> $(DJANGO_SETTINGS_FILE);\
		$(PYTHON) $(SCRIPTS)/generateSecretDjangoKey.py >> $(DJANGO_SETTINGS_FILE);\
		echo "'" >> $(DJANGO_SETTINGS_FILE),)

# this target is used to check if the user wants the development or staging settings
# the "dev" parameter is used if both parameters are used ("dev" and "stage")
check-dev_staging:
	@# only apply if no variable was set before
	@$(if $(or $(filter $(DEVELOPMENT),true),$(filter $(STAGING),true)),,\
		@$(if $(filter $(MAKECMDGOALS),dev),\
			$(eval DEVELOPMENT = true),\
			@$(if $(filter $(MAKECMDGOALS),stage),\
				$(eval STAGING = true),\
				@$(if $(wildcard $(MAKE_SETTINGS_FILE)),\
					$(eval DEVELOPMENT = $(shell grep "development=" $(MAKE_SETTINGS_FILE) | grep -o '".*"' |sed 's/"//g')) \
					@$(if $(filter $(DEVELOPMENT),true),,\
						$(eval STAGING = $(shell grep "staging=" $(MAKE_SETTINGS_FILE) | grep -o '".*"' |sed 's/"//g'))) \
					,))))
	# save the settings
	@$(MAKE) DEVELOPMENT=$(DEVELOPMENT) STAGING=$(STAGING) save-dev_stage-setting

# save the development or staging state in a separate file
save-dev_stage-setting:
	@$(if $(filter $(DEVELOPMENT),true),\
		echo 'development="true"' > $(MAKE_SETTINGS_FILE),\
		@$(if $(filter $(STAGING),true),\
			echo 'staging="true"' > $(MAKE_SETTINGS_FILE),))

# link the custom git hooks to the .git directory
link-git-hooks: ##@development Link all Git-Hooks found in tools/git-hooks/ to .git/hooks/.
	@# link the custom hooks to the .git/hooks directory
	@$(foreach hook,$(CUSTOM_GIT_HOOKS), ln -sf ../../$(hook) $(GITHOOKS);)

run: ##@django Run the default django server.
	cd $(DJANGO_BASE) && $(PYTHON) $(DJANGO_MANAGE) runserver --settings=$(DJANGO_SETTINGS)

startapp: ##@django <appname> Create a new django application.
	cd $(DJANGO_BASE) && $(PYTHON) $(DJANGO_MANAGE) startapp $(filter-out $@,$(MAKECMDGOALS)) --settings=$(DJANGO_SETTINGS)

makemigrations: ##@django Make the django migrations.
	cd $(DJANGO_BASE) && $(PYTHON) $(DJANGO_MANAGE) makemigrations --settings=$(DJANGO_SETTINGS)

migrate: ##@django Migrate the django database.
	cd $(DJANGO_BASE) && $(PYTHON) $(DJANGO_MANAGE) migrate --settings=$(DJANGO_SETTINGS)

test: ##@django Run the django tests. An app can be specified with <appname>. Add "dev" to avoid the generation of migrations.
test: $(filter $(DJANGO_INSTALLED_APPS),$(MAKECMDGOALS)) $(filter $(DJANGO_INSTALLED_APPS_WILDCARD),$(MAKECMDGOALS)) check-dev_staging
	@$(if $(filter $(DEVELOPMENT),true),\
		cd $(DJANGO_BASE) && $(PYTHON) -Wall $(DJANGO_MANAGE) test --noinput --nomigrations $(APPNAME) --settings=$(DJANGO_SETTINGS),\
		cd $(DJANGO_BASE) && $(PYTHON) -Wall $(DJANGO_MANAGE) test --noinput $(APPNAME) --settings=$(DJANGO_SETTINGS))

# this target drops any error messages that are from imported packages.
# but this target shall not replace the above one due to the following reasons:
#   1. the error-messages are not printed immediately
#   2. some of those error-codes, like E,F or success-code are dropped, since those lines might contain error-messages of imported packages
test-ign_imp_errs: ##@django Run the django tests without error-messages from imported packages (perhaps even more). An app can be specified with <appname>.
test-ign_imp_errs: $(filter $(DJANGO_INSTALLED_APPS),$(MAKECMDGOALS)) $(filter $(DJANGO_INSTALLED_APPS_WILDCARD),$(MAKECMDGOALS)) check-dev_staging
	@$(if $(filter $(DEVELOPMENT),true),\
		cd $(DJANGO_BASE) && $(PYTHON) -Wall $(DJANGO_MANAGE) test --noinput --nomigrations $(APPNAME) --settings=$(DJANGO_SETTINGS),\
		cd $(DJANGO_BASE) && $(PYTHON) -Wall $(DJANGO_MANAGE) test --noinput $(APPNAME) --settings=$(DJANGO_SETTINGS) |& grep -v virtualenv)

func_tests: ##@django run the django functional tests.
	make test functional_tests

make-messages: ##@django <lang-code> Make the django messages for a specific language.
	@$(eval LANG := $(filter-out $@,$(MAKECMDGOALS)))
	@$(if $(LANG),,\
		echo "Using default language 'en'" \
		$(eval LANG := en))
	cd $(DJANGO_BASE) && $(PYTHON) $(DJANGO_MANAGE) makemessages -l $(LANG) --settings=$(DJANGO_SETTINGS) -i 'htmlcov' -i 'manage.py'

compile-messages: ##@django Compile the django messages.
	cd $(DJANGO_BASE) && $(PYTHON) $(DJANGO_MANAGE) compilemessages --settings=$(DJANGO_SETTINGS)

coverage: ##@coverage Run coverage on the django tests. An app can be specified with <appname>. But please note that it is not possible to chain multiple coverage runs without combining them, even without the coverage-erase dependency.
coverage: $(filter $(DJANGO_INSTALLED_APPS),$(MAKECMDGOALS)) $(filter $(DJANGO_INSTALLED_APPS_WILDCARD),$(MAKECMDGOALS)) coverage-erase check-dev_staging
	@$(if $(filter $(DEVELOPMENT),true),\
		cd $(DJANGO_BASE) && $(COVERAGE) run $(DJANGO_MANAGE) test --noinput --nomigrations $(APPNAME) --settings=$(DJANGO_SETTINGS),\
		cd $(DJANGO_BASE) && $(COVERAGE) run $(DJANGO_MANAGE) test --noinput $(APPNAME) --settings=$(DJANGO_SETTINGS))

coverage_func: ##@coverage Run coverage on the django tests including the functional_tests
coverage_func: $(filter $(DJANGO_INSTALLED_APPS),$(MAKECMDGOALS)) $(filter $(DJANGO_INSTALLED_APPS_WILDCARD),$(MAKECMDGOALS)) coverage-erase check-dev_staging
	@$(if $(filter $(DEVELOPMENT),true),\
		cd $(DJANGO_BASE) && COVERAGE_FILE=.coverage_apps $(COVERAGE) run $(DJANGO_MANAGE) test --noinput --nomigrations $(APPNAME) --settings=$(DJANGO_SETTINGS) ;\
		cd $(DJANGO_BASE) && COVERAGE_FILE=.coverage_funcs $(COVERAGE) run $(DJANGO_MANAGE) test --noinput --nomigrations functional_tests --settings=$(DJANGO_SETTINGS) ;\
		cd $(DJANGO_BASE) && $(COVERAGE) combine .coverage_apps .coverage_funcs,\
		cd $(DJANGO_BASE) && COVERAGE_FILE=.coverage_apps $(COVERAGE) run $(DJANGO_MANAGE) test --noinput $(APPNAME) --settings=$(DJANGO_SETTINGS) ;\
		cd $(DJANGO_BASE) && COVERAGE_FILE=.coverage_funcs $(COVERAGE) run $(DJANGO_MANAGE) test --noinput functional_tests --settings=$(DJANGO_SETTINGS) ;\
		cd $(DJANGO_BASE) && $(COVERAGE) combine .coverage_apps .coverage_funcs)\


coverage-report: ##@coverage Get the coverage report.
coverage-report: coverage_func
	cd $(DJANGO_BASE) && $(COVERAGE) report

coverage-html: ##@coverage Get the coverage report as HTML.
coverage-html: coverage_func
	cd $(DJANGO_BASE) && $(COVERAGE) html

coverage-xml: ##@coverage Get the coverage report as XML.
coverage-xml: coverage_func
	cd $(DJANGO_BASE) && $(COVERAGE) xml

coverage-erase: ##@coverage Delete the last coverage report.
coverage-erase:
	cd $(DJANGO_BASE) && $(COVERAGE) erase

# create the css files
css: ##@main Create the CSS files.
	$(eval SASSC := $(shell command -v sassc 2> /dev/null))
	@$(if $(SASSC),\
		$(foreach file,$(SCSS_FILES), \
			sassc $(DJANGO_SCSS)/$(file).scss $(DJANGO_STATIC)/css/$(file).css;), \
		$(warning "Warning: sassc is not installed!"))

list_bugs: ##@other List all occurrences of the tag "TODO BUG".
	cd src && grep --color -n -i -R -H "TODO BUG" *

list_missing_testcases: ##@other List all occurrences of the tag "TODO TESTCASE".
	cd src && grep --color -n -i -R -H "TODO TESTCASE" *

add_license_header: ##@other Insert the license header into all source files.
add_license_header: $(DJANGO_BASE)/add_header.sh
	cd $(DJANGO_BASE) && ./add_header.sh

check_requirements: ##@other Check whether our requirements are up to date or not.
	for reqs in development production staging; do \
		echo "========= $$reqs ========="; \
		piprot requirements/$$reqs.req | grep -v "up to date"; \
	done

# default target for targets that are meant as parameters
.DEFAULT:
	@# do nothing here

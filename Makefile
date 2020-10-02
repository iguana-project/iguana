###########
# Variables
###########

# global variables
BASE = $(shell pwd)

# the python makefile
PYTHON_MAKE = $(BASE)/src/make.py

# look for the python3 executable
PYTHON3 = $(shell command -v python3 2> /dev/null)
ifeq ($(strip $(PYTHON3)),)
$(error "Error: python3 is not installed!")
else
# do not show bytes warnings on Travis, because then the build/test will fail
ifndef TRAVIS
# the -bb "-b Issue warnings about str(bytes_instance), str(bytearray_instance) and comparing bytes/bytearray  with str. (-bb: issue errors)"
# s.a. https://docs.djangoproject.com/en/2.0/releases/2.0/#removed-support-for-bytestrings-in-some-places
PYTHON3 += -bb
endif
endif


#######################
# No changes from here!
#######################

# hack for making make silent (gives better output when specifying a django app as target)
MAKEFLAGS += -s


#########
# Targets
#########

# XXX Don't forget to update the targets as soon as the makefile or make.py is extended
# because then bash completion is supported
TARGETS = help production staging development run django create-app migrations test messages collectstatic requirements setup-virtualenv set-webdriver coverage css list add-license new-release

# phony targets
.PHONY: $(TARGETS)

# pass all arguments to the target
.DEFAULT_GOAL := help
$(TARGETS):
	# fix for using '-' and '--' arguments
	# you can set optional parameters with '+' or '++', so these parameters get passed to the python makefile
	$(eval ARGS := $(patsubst ++%,--%,$(MAKECMDGOALS)))
	$(eval ARGS := $(patsubst +%,-%,$(ARGS)))

	$(PYTHON3) $(PYTHON_MAKE) $(ARGS)


# default target for targets that are meant as parameters
.DEFAULT:
	@# do nothing here

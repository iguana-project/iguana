#!/usr/local/bin/python
from os import path, symlink, system, sep, chown, setgid, setuid, environ, stat, walk
from distutils.dir_util import copy_tree, remove_tree
from pwd import getpwuid
from subprocess import Popen
from random import SystemRandom
import string
import json
from collections import OrderedDict


BASE_DIR = path.abspath(environ.get("APP_DIR"))
IGUANA_DIR = path.join(BASE_DIR, "src")
IGUANA_FILES_DIR = path.abspath(environ.get("IGUANA_FILES_DIR"))

IGUANA_PUID = int(environ.get("PUID"))
IGUANA_PGID = int(environ.get("PGID"))

VARIANT = environ.get("VAIRANT")
USE_NGINX = bool(environ.get("USE_NGINX"))

FIRST_RUN_FILE = path.join(BASE_DIR, ".initialized")


# move /iguana/files to /files directory and symlink to it
if not path.islink(_iguana_files_dir):
    print("Creating default files on the volume.")
    _iguana_files_dir = path.join(BASE_DIR, "files")
    copy_tree(_iguana_files_dir, IGUANA_FILES_DIR)
    remove_tree(_iguana_files_dir)
    symlink(IGUANA_FILES_DIR, _iguana_files_dir)


# create Iguana user
try:
    # check if it exists
    getpwuid(IGUANA_PUID)
    print("User 'iguana' already exists.")
except Exception:
    print("Creating user 'iguana'.")
    system("addgroup --gid " + str(IGUANA_PGID) + " iguana")
    system("adduser --disabled-password --no-create-home --gecos '' --uid " + str(IGUANA_PUID) + " -G iguana iguana")


# chown the application path to the Iguana user
print('Setting file permissions.')
for dir in [BASE_DIR, IGUANA_FILES_DIR]:
    if stat(dir).st_uid != IGUANA_PUID or \
            stat(dir).st_gid != IGUANA_PGID:
        # recursive chown
        for root, dirs, files in walk(dir):
            for d in dirs:
                chown(path.join(root, d), IGUANA_PUID, IGUANA_PGID, follow_symlinks=False)
            for f in files:
                chown(path.join(root, f), IGUANA_PUID, IGUANA_PGID, follow_symlinks=False)

        # don't forget the root directory
        chown(dir, IGUANA_PUID, IGUANA_PGID, follow_symlinks=False)


# switch to user iguana
setgid(IGUANA_PGID)
setuid(IGUANA_PUID)


# reinitialize settings on first run
if not path.isfile(FIRST_RUN_FILE):
    # load side _side_module
    _spec = importlib.util.spec_from_file_location('manage_settings',
                                                   path.join(IGUANA_DIR, "lib", "manage_settings.py"))
    _side_module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_side_module)

    # recreate the django secret key (override!)
    _django_settings_file = path.join(IGUANA_DIR, "common", "settings", "__init__.py")
    _iguana_settings_file = path.join(IGUANA_FILES_DIR, "settings.json")
    _is_development = VARIANT == "development"
    _side_module.initialize_secret_key(_django_settings_file, _iguana_settings_file, _is_development, True)

    # mark as reinitialized
    open(FIRST_RUN_FILE, 'a').close()


# start Iguana
print("Starting Iguana.")
if VARIANT != "development" and USE_NGINX:
    # start nginx
    Popen("nginx", "-c", path.join(IGUANA_FILES_DIR, "nginx.conf"))

if VARIANT == "development":
    system("python " + path.join(IGUANA_DIR, "make.py") + " run 0.0.0.0:80")
else:
    system("python " + path.join(IGUANA_DIR, "make.py") + " run")

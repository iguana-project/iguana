#!/usr/local/bin/python
from os import path, symlink, system, chown, setgid, setuid, environ, stat, walk
from distutils.dir_util import copy_tree, remove_tree
from pwd import getpwuid
from subprocess import Popen, STDOUT
from importlib import util as import_util


BASE_DIR = path.abspath(environ.get("APP_DIR"))
FILES_DIR = path.abspath(environ.get("FILES_DIR"))
IGUANA_DIR = path.join(BASE_DIR, "src")

IGUANA_PUID = int(environ.get("PUID"))
IGUANA_PGID = int(environ.get("PGID"))

VARIANT = environ.get("VARIANT")
USE_NGINX = bool(environ.get("USE_NGINX"))

SETTING_TIME_ZONE = environ.get("TZ")
SETTING_LANGUAGE = environ.get("LANG")

FIRST_RUN_FILE = path.join(BASE_DIR, ".initialized")


# move /iguana/files to /files directory and symlink to it
_iguana_files_dir = path.join(BASE_DIR, "files")
if not path.islink(_iguana_files_dir):
    print("Creating default files on the volume.")
    copy_tree(_iguana_files_dir, FILES_DIR)
    remove_tree(_iguana_files_dir)
    symlink(FILES_DIR, _iguana_files_dir)


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
for dir in [BASE_DIR, FILES_DIR]:
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

# start nginx and cron daemon (for logrotate) as root
if VARIANT != "development" and USE_NGINX:
    # start nginx
    Popen(["nginx", "-c", path.join(FILES_DIR, "nginx.conf")])
    # start cron for logrotate
    Popen(["crond", "-L", path.join(FILES_DIR, "logs", "cron.log")])


# switch to user iguana
setgid(IGUANA_PGID)
setuid(IGUANA_PUID)


# reinitialize settings on first run
if not path.isfile(FIRST_RUN_FILE):
    print("Initializing Iguana.")

    # load side _side_module
    _spec = import_util.spec_from_file_location('manage_settings',
                                                path.join(IGUANA_DIR, "lib", "manage_settings.py"))
    _side_module = import_util.module_from_spec(_spec)
    _spec.loader.exec_module(_side_module)

    # recreate the django secret key (override!)
    _django_settings_file = path.join(IGUANA_DIR, "common", "settings", "__init__.py")
    _iguana_settings_file = path.join(FILES_DIR, "settings.json")
    _is_development = VARIANT == "development"
    _side_module.initialize_secret_key(_django_settings_file, _iguana_settings_file, _is_development, True)

    # set additional settings
    _settings = {
        'TIME_ZONE': SETTING_TIME_ZONE,
        'LANGUAGE_CODE': SETTING_LANGUAGE
    }
    if _is_development:
        _side_module.set_django_settings(_django_settings_file, _settings)
    else:
        _side_module.set_django_settings(_iguana_settings_file, _settings)

    # mark as reinitialized
    open(FIRST_RUN_FILE, 'x').close()


# start Iguana
print("Starting Iguana.")
if VARIANT == "development":
    system("python " + path.join(IGUANA_DIR, "make.py") + " run 0.0.0.0:8000")
else:
    system("python " + path.join(IGUANA_DIR, "make.py") + " run")

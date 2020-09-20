#!/usr/local/bin/python
from os import path, symlink, system, chown, setgid, setuid, environ, stat, walk, makedirs, remove
from distutils.file_util import copy_file
from pwd import getpwnam
from subprocess import Popen, STDOUT
from importlib import util as import_util
from shutil import move
from grp import getgrnam


BASE_DIR = path.abspath(environ.get("APP_DIR"))
FILES_DIR = path.abspath(environ.get("FILES_DIR"))
IGUANA_DIR = path.join(BASE_DIR, "src")

IGUANA_USER = IGUANA_GROUP = "iguana"
IGUANA_PUID = int(environ.get("PUID"))
IGUANA_PGID = int(environ.get("PGID"))

VARIANT = environ.get("VARIANT")
USE_NGINX = environ.get("USE_NGINX").lower() in ("true", "1")

SETTING_TIME_ZONE = environ.get("TZ")
SETTING_LANGUAGE = environ.get("LANG")

FIRST_RUN_FILE = path.join(FILES_DIR, ".initialized")
FORCE_CHOWN = False


# prepare the /files directory
_iguana_files_dir = path.join(BASE_DIR, "files")
# rename the existing /BASE_DIR/files directory to /BASE_DIR/files_default
if not path.islink(_iguana_files_dir):
    move(_iguana_files_dir, path.join(BASE_DIR, "files_default"))

    # symlink /files to /BASE_DIR/files
    symlink(FILES_DIR, _iguana_files_dir)

# after the previous step files dir is moved to /BASE_DIR/files_default
_iguana_files_dir = path.join(BASE_DIR, "files_default")

# these files must exist everytime when the Docker container is started
print("Creating default files on the volume.")
_necessary_files = ["logs", path.join("media", "avatars", "default.svg")]
# the settings.json file is also mandatory if we're not in development mode
if VARIANT != "development":
    _necessary_files.append("settings.json")
# if Nginx is installed, the config is also necessary
if USE_NGINX:
    _necessary_files.append("nginx.conf")
for df in _necessary_files:
    # copy the file if it doesn't exists or create the directory
    if not path.exists(path.join(FILES_DIR, df)):
        src_path = path.join(_iguana_files_dir, df)
        if path.isdir(src_path):
            makedirs(path.join(FILES_DIR, df), exist_ok=True)
        else:
            makedirs(path.dirname(path.join(FILES_DIR, df)), exist_ok=True)
            copy_file(src_path, path.join(FILES_DIR, df))

        # force a chown after a file was copied
        FORCE_CHOWN = True

        # force reinitialization of the settings later if the settings.json file was recovered
        if df == "settings.json" and path.isfile(FIRST_RUN_FILE):
            remove(FIRST_RUN_FILE)


# create Iguana group
try:
    getgrnam(IGUANA_GROUP)
    print("Group '%s' already exists." % IGUANA_GROUP)
except KeyError:
    print("Creating group '%s'." % IGUANA_GROUP)
    system("groupadd --non-unique --gid %s %s" % (str(IGUANA_PGID), IGUANA_GROUP))

# create Iguana user
try:
    getpwnam(IGUANA_USER)
    print("User '%s' already exists." % IGUANA_USER)
except KeyError:
    print("Creating user '%s'." % IGUANA_USER)
    system("useradd --no-create-home --shell /sbin/nologin --non-unique --uid %s --gid %s %s" %
           (str(IGUANA_PUID), str(IGUANA_PGID), IGUANA_USER))


# chown the application path to the Iguana user
print('Setting file permissions.')
for dir in [BASE_DIR, FILES_DIR]:
    if stat(dir).st_uid != IGUANA_PUID or \
            stat(dir).st_gid != IGUANA_PGID or \
            FORCE_CHOWN:
        # recursive chown
        for root, dirs, files in walk(dir):
            for d in dirs:
                chown(path.join(root, d), IGUANA_PUID, IGUANA_PGID, follow_symlinks=False)
            for f in files:
                chown(path.join(root, f), IGUANA_PUID, IGUANA_PGID, follow_symlinks=False)

        # don't forget the root directory
        chown(dir, IGUANA_PUID, IGUANA_PGID, follow_symlinks=False)

# start helper processes as root
if VARIANT != "development":
    if USE_NGINX:
        # start nginx if it is used
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
    _is_development = VARIANT == "development"
    _side_module.initialize_secret_key(_is_development, True)

    # set additional settings
    _settings = {
        'TIME_ZONE': SETTING_TIME_ZONE,
        'LANGUAGE_CODE': SETTING_LANGUAGE
    }
    _side_module.set_django_settings(_is_development, _settings)

    # mark as reinitialized
    open(FIRST_RUN_FILE, 'x').close()


# start Iguana
print("Starting Iguana.")
# apply migrations first (this may be necessary after an update, or a database change)
system("python " + path.join(IGUANA_DIR, "make.py") + " migrations apply")

if VARIANT == "development":
    system("python " + path.join(IGUANA_DIR, "make.py") + " run 0.0.0.0:8000")
else:
    system("python " + path.join(IGUANA_DIR, "make.py") + " run")

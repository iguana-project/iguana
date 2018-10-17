import sys
import os

import argparse


# setup the arguments
parser = argparse.ArgumentParser(description="Get all installed applications of a django installation.")
parser.add_argument('django_root',
                    help="Root directory of the django installation",
                    metavar="<django-installation>")
myargs = parser.parse_args(sys.argv[1:])

# get the arguments
djangoRoot = myargs.django_root

# check for djano manage.py
if not os.path.isfile(os.path.join(djangoRoot, "manage.py")):
    print("No valid django root directory provided!", file=sys.stderr)
    sys.exit(1)

# get all folders in the django root directory
for path in os.listdir(djangoRoot):
    fullPath = os.path.join(djangoRoot, path)
    # check if these folders contain a __init__.py
    if os.path.isfile(os.path.join(fullPath, "__init__.py")):
        print(path)

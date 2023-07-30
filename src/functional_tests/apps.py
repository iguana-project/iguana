"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin, Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under BSD-2-Clause License.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
   2. Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer
      in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import inspect
import pkgutil
import sys

from django.apps import AppConfig
from django.test import tag

from lib.selenium_test_case import SeleniumTestCase


def getModules(parentPackageModule):
    """
    This method searches recursively through the packages and collects all Python modules.
    params:
        parentPackageModule: the package to start with
    """
    moduleList = []
    for _, moduleName, isPackage in pkgutil.iter_modules(parentPackageModule.__path__):
        fullModuleName = parentPackageModule.__name__ + '.' + moduleName

        # import of the module is necessary to access its members
        __import__(fullModuleName)
        moduleObject = sys.modules[fullModuleName]

        # check if the module is a package
        if isPackage:
            moduleList += getModules(moduleObject)
        else:
            moduleList.append(moduleObject)

    return moduleList


class FunctionalTestsConfig(AppConfig):
    name = 'functional_tests'

    def ready(self):
        # tag all functional tests with 'functional'
        # collect all modules of this package
        modules = getModules(sys.modules[self.name])

        # iterate over the moules
        for module in modules:
            # get the classes of the module
            clsmembers = inspect.getmembers(module, inspect.isclass)
            for clsName, cls in clsmembers:
                # check if it's a selenium test case
                if cls.__module__ == module.__name__ and \
                        issubclass(cls, SeleniumTestCase):
                    # tag it
                    setattr(module, clsName, tag("functional")(cls))

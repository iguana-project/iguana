"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""


class Singleton(type):
    """
    This is the base meta class to create a singleton.

    Example:
        class ASingleton(metaclass=Singleton):
            pass

    Access the instance of the above example class via ASingleton.instance
    """
    __instance = None

    @property
    def instance(self):
        if not self.__instance:
            self.__instance = type.__call__(self)
        return self.__instance

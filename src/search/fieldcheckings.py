"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""


# This is pretty much just a logical hint for classes to be searchable.
# In most cases these functionalities are overwritten in the classes mixed this mixin in
class SearchableMixin():
    # NOTE: This shall be overwritten in the classes that mix this mixin in, otherwise this mixin is not useful there
    searchable_fields = []

    # This shall be overwritten in most of the classes that mix this mixin in
    def search_allowed_for_user(self, user):
        return True

    # This can be overwritten to use another function than __str__() as result title
    def get_search_title(self):
        return self.__str__()

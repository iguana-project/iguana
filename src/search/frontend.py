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
from search import parser

from django.apps import apps
from django.db.models import Q
from django.urls import reverse

from search.models import Search
from search.fieldcheckings import SearchableMixin


app_list = {}
searchable_fields = {}
# get all models that implement the SearchableMixin
for app in apps.get_models():
    if issubclass(app, SearchableMixin) and \
            hasattr(app, "searchable_fields"):
        app_name = app.get_search_name()
        app_list[app_name] = app
        searchable_fields[app_name] = app.searchable_fields


class SearchFrontend():
    # TODO getattr and hasattr is mixed, this didn't happen because of runtime issues
    #      http://stackoverflow.com/questions/903130/hasattr-vs-try-except-block-to-deal-with-non-existent-attributes
    def check_field_searchability(instance, field):
        if instance not in app_list.keys():
            return False

        attr = app_list[instance]
        field_path = field.split('__')
        lastSearchable = False

        for elem in field_path:
            attr_object = None

            if str(attr).startswith("<django.db.models"):
                # we have some kind of foreign key
                if ".Reverse" in str(attr):
                    # we have a reverse relation
                    attr_object = attr.field.model
                else:
                    # we have a normal relationship
                    attr_object = attr.field.remote_field.model
            else:
                # we have a normal field
                attr_object = attr

            lastSearchable = elem in attr_object.searchable_fields
            if lastSearchable is False:
                return False

            try:
                attr = getattr(attr_object, elem)
            except AttributeError as e:
                return False

        try:
            attr.field_name
        except AttributeError:
            return False

        return lastSearchable

    def search_all_fields_for(expression):
        retval = []

        # split expression at 'AND' and 'OR' and check results
        expr_or = expression.split(' OR ')

        for app in app_list.values():
            q_expression = None
            for field in app.searchable_fields:
                if SearchFrontend.check_field_searchability(app.get_search_name(), field):

                    q_or = None
                    for part_or in expr_or:
                        # ORs, split at ANDs
                        expr_and = part_or.split(' AND ')
                        q = None

                        for part in expr_and:
                            # skip search if we have less than 3 characters in our expression part
                            if len(part) < 3:
                                raise ValueError()

                            if q is None:
                                q = Q(**{field + "__icontains": part})
                            else:
                                q = q & Q(**{field + "__icontains": part})

                        if q_or is None:
                            q_or = q
                        else:
                            q_or = q_or | q

                    if q_expression is None:
                        q_expression = q_or
                    else:
                        q_expression = q_expression | q_or

            if q_expression is not None:
                # order descending by pk by default
                retval.extend(list(app.objects.filter(q_expression).order_by('-pk').distinct()))

        return retval

    def query(expression, user):
        try:
            expr = parser.compile(expression)
            result = app_list[parser.obj_to_query].objects.filter(expr).distinct()

            # order results
            for s in parser.sort_by:
                result = result.order_by(s)

            # save as non-persistent search object
            if Search.objects.filter(searchexpression=expression).count() == 0:
                Search(description="Autosave", searchexpression=expression, creator=user).save()
        except Exception as e:
            # parsing exception, search all fields for expression, case of full-text-search (can't be parsed)
            # full-text search aren't stored for reuse currently
            # if len(expression):
            #    Search(description="Autosave", searchexpression=expression, creator=user).save()

            # skip search if we have less than 3 characters in our expression
            if len(expression) < 3:
                raise ValueError()

            result = SearchFrontend.search_all_fields_for(expression)

        # check user permissions
        valid_items = [r for r in result if r.search_allowed_for_user(user)]

        # limit results
        if parser.limit != -1:
            valid_items = valid_items[:parser.limit]

        # prepare a list of lists containing information about discovered items
        retval = []
        for i in valid_items:
            linktext = i.get_search_title()
            link = i.get_absolute_url()
            objname = i.__class__.get_search_name()
            relative_project = i.get_relative_project()

            retval.append([linktext, link, objname, relative_project])

        return retval

"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.core.paginator import EmptyPage, Paginator
from itertools import chain


class ShowMoreMixin(object):
    """
    This Mixin creates a show more pagination for a given list of items.

    Simply add the following HTML snippet to your template to add the 'Show More' button/link:
        <ul class="list-group">
            {% for item in page_items %}
                <li id="id_item_{{ forloop.counter }}" class="list-group-item">{{ item }}</li>
            {% endfor %}
            {% if page_items.has_next %}
                <li class ="list-group-item">
                    <a href="?page={{ page_items.next_page_number }}#id_item_{{ page_items|length|add:"1" }}">
                        {% trans "Show More" %}
                    </a>
                </li>
            {% endif %}
        </ul>
    """

    item_list = None
    """
    The list of items that should be managed by the paginator.
    This list can be filled in the get() method of a view. But it must be filled before calling get_context_data().
    """

    items_per_page = 10
    """
    The amount of items displayed on each 'page' (added by each click on 'Show More').
    Default: 10 items per page
    """

    def get_context_data(self, **kwargs):
        context = super(ShowMoreMixin, self).get_context_data(**kwargs)

        if self.item_list:
            paginator = Paginator(self.item_list, self.items_per_page)

            page = self.request.GET.get('page')
            if not page or \
                    not page.isdigit():
                items = paginator.page(1)
            else:
                try:
                    items = self.getItemsUntilPage(paginator, page)
                except EmptyPage:
                    items = self.getItemsUntilPage(paginator, paginator.num_pages)

            context['page_items'] = items

        return context

    def getItemsUntilPage(self, paginator, pageNumber):
        """
        Get all items until a specified page.
        """
        # get the requested page
        items = paginator.page(pageNumber)

        # then go back to the first page and add those items too
        for i in reversed(range(1, int(pageNumber))):
            items.object_list = list(chain(paginator.page(i).object_list, items.object_list))

        return items

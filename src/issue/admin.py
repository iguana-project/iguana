"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.contrib import admin
from .models import Issue, Comment, Attachment

# Register your models here.
admin.site.register(Issue)
admin.site.register(Comment)
admin.site.register(Attachment)

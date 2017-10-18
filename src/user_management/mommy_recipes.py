"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from model_mommy.recipe import Recipe, seq
from django.contrib.auth import get_user_model

user = Recipe(get_user_model(), username=seq('user'), email=seq('user@exmple.org'))

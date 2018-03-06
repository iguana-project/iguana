"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from refreshtoken.models import RefreshToken


def jwt_response_payload_handler(token, user=None, request=None):
    payload = {
        'token': token,
    }

    app = 'iguana'

    try:
        refresh_token = user.refresh_tokens.get(app=app).key
    except RefreshToken.DoesNotExist:
        refresh_token = RefreshToken(app=app, user=user)
        refresh_token.save()

    payload['refresh_token'] = refresh_token

    return payload

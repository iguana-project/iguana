"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.dispatch import Signal
from django.dispatch import receiver


basic_args = ["instance", "user"]
create = Signal(providing_args=basic_args)
modify = Signal(providing_args=basic_args + ["changed_data"])
start = Signal(providing_args=basic_args)
stop = Signal(providing_args=basic_args)

signals = [create, modify, start, stop]


def connector(sender, **kwargs):
    # If this happens at startup, it is impossible to run the website
    # from a scratch database. So this function lazily connects the Integrations
    # when the first signal is sent.
    # If you want to subscribe to these signals in other parts of the site, do
    # it here.

    # Slack integration
    from integration.models import SlackIntegration
    for si in SlackIntegration.objects.all():
        si.connect_signals()

    # activity stream
    from landing_page.handler import ActStreamHandler
    ActStreamHandler.connect_signals()

    # disconnect the connector
    for signal in signals:
        signal.disconnect(connector, dispatch_uid="signal-init")
    # resend the signal so the newly connected receivers actually receive it
    signal = kwargs['signal']
    del kwargs['signal']
    signal.send(sender=sender, **kwargs)


def setup_connectors():
    for signal in signals:
        signal.connect(connector, weak=False, dispatch_uid="signal-init")


def fields_to_changed_data(old, fields):
    """
    Turns a model instance and a list of fields or attributes into a dictionary
    that can be used with the modify signal.
    """
    changed_data = {}
    for field in fields:
        old_field = old.__getattribute__(field)
        old_str = str(old_field)
        # Ducktyping for RelatedManager
        if hasattr(old_field, "add") and \
                hasattr(old_field, "create") and \
                hasattr(old_field, "remove") and \
                hasattr(old_field, "clear") and \
                hasattr(old_field, "set"):
            old_str = ", ".join([str(e) for e in old_field.all()])
        changed_data[field] = old_str
    return changed_data

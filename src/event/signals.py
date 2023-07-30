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

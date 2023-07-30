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
from django.urls import reverse_lazy, reverse
from timelog.models import *
from django.contrib import messages
from django.core.cache import cache

from datetime import *
from .forms import *
import json
from django.core import serializers
from issue.models import *
from project.models import *
from django.http import HttpResponse
import pytz
from django.utils import timezone
from django.contrib.auth import get_user_model
import dateutil.parser

from lib.custom_model import get_r_object_or_404


def get_action_data(project, user):
    if project:
        result = cache.get('action_data_'+user.username+'_'+project.name_short)
        if result:
            return result
    else:
        result = cache.get('action_data_'+user.username)
        if result:
            return result

    result = {}
    act_count = 0
    maximum = 0
    if project:
        data = json.loads(user.activity)[project.name_short]
    else:
        data2 = json.loads(user.activity)
        data = []
        for key, values in data2.items():
            data += values
        data.sort(key=lambda x: x[0])

    if(len(data) > 0):
        new_day = dateutil.parser.parse(data[0][0]).replace(hour=1, minute=1, second=1, microsecond=1).date()
    for timestamp, issue in data:
        date_object = dateutil.parser.parse(timestamp)
        act_day = date_object.date()
        date = date_object.timestamp()
        if date in result:
            result[date] += 1
        else:
            result[date] = 1
        if(act_day == new_day):
            act_count += 1
        else:
            if (act_count > maximum):
                maximum = act_count
            new_day = act_day
            act_count = 0
            act_count += 1

    if (act_count > maximum):
        maximum = act_count
    result['START_MONTH'] = str((timezone.now()-timedelta(days=335)).date())
    result['USERNAME'] = user.username
    result['MAXIMUM'] = maximum

    if project:
        cache.set('action_data_'+user.username+'_'+project.name_short, result, 60*60*24*3)
    else:
        cache.set('action_data_'+user.username, result, 60*60*24*3)
    return result


def get_timelog_data(project, user):
    if project:
        result = cache.get('timelog_data_'+user.username+'_'+project.name_short)
        if result:
            return result
    else:
        result = cache.get('timelog_data_'+user.username)
        if result:
            return result

    if project:
        data = Timelog.objects.filter(issue__project__name_short=project.name_short,
                                      user=user).order_by('created_at')
    else:
        data = Timelog.objects.filter(user=user).order_by('created_at')

    result = {}
    if(len(data) > 0):
        timestamp = data[0].created_at.replace(hour=1, minute=1, second=1, microsecond=1).timestamp()
    maximum = 0
    act_count = 0
    for d in data:
        act_day = d.created_at.replace(hour=1, minute=1, second=1, microsecond=1).timestamp()
        if (d.created_at.timestamp() in result):
            result[d.created_at.timestamp()] += d.time.total_seconds()/60
        else:
            result[d.created_at.timestamp()] = d.time.total_seconds()/60
        if(act_day == timestamp):
            act_count += d.time.total_seconds()/60
        else:
            if (act_count > maximum):
                maximum = act_count
            timestamp = act_day
            act_count = 0
            act_count += d.time.total_seconds()/60

    if (act_count > maximum):
        maximum = act_count

    result['START_MONTH'] = str((timezone.now()-timedelta(days=335)).date())
    result['USERNAME'] = user.username
    result['MAXIMUM'] = maximum

    if project:
        cache.set('timelog_data_'+user.username+'_'+project.name_short, result, 60*60*24*3)
    else:
        cache.set('timelog_data_'+user.username, result, 60*60*24*3)

    return result


def d3_json_activity(request):
    if not request.user.is_authenticated:
        resp = json.dumps("login!")
        return HttpResponse(resp, content_type='application/json')

    proj = request.GET.get('project', None)
    project = Project.objects.filter(name_short=proj)
    if project.exists() and project.first().developer_allowed(request.user):
        project = project.first()
    else:
        project = None

    data_type = request.GET.get('data', None)

    user = request.GET.get('user', request.user.username)
    user = get_r_object_or_404(request.user, get_user_model(), username=user)
    if not user.show_activity_to_other_users and user != request.user:
        return HttpResponse(json.dumps(""), content_type='application/json')

    if data_type == 'actions':
        result = get_action_data(project, user)
    else:
        result = get_timelog_data(project, user)
    resp = json.dumps(result)
    return HttpResponse(resp, content_type='application/json')


def d3_json_last_7_days(request):

    if not request.user.is_authenticated:
        resp = json.dumps("login!")
        return HttpResponse(resp, content_type='application/json')

    now = timezone.now()
    delta = timedelta(6)
    start_date = now - delta
    start_date = start_date.replace(hour=0, minute=0, second=0)

    proj = request.GET.get('project', None)
    project = Project.objects.filter(name_short=proj)

    test = project.exists() and project.first().developer_allowed(request.user)

    if test:
        data = Timelog.objects.filter(issue__project__name_short=proj,
                                      user=request.user,
                                      created_at__gt=start_date).order_by('created_at')
    else:
        data = Timelog.objects.filter(user=request.user, created_at__gt=start_date).order_by('created_at')

    jsonString = serializers.serialize("json", data)
    jsonObject = json.loads(jsonString)
    for entry in jsonObject:
        issue_id = entry['fields']['issue']
        iss = Issue.objects.get(id=issue_id)
        entry['fields']['issue_title'] = iss.title
        entry['fields']['issue_short'] = iss.get_ticket_identifier()
        proj = Project.objects.get(id=iss.project.id)
        entry['fields']['issue_project_name'] = proj.name
        entry['fields']['issue_url'] = reverse('issue:detail',
                                               kwargs={"project": proj.name_short, "sqn_i": iss.number}
                                               )

    resp = json.dumps(jsonObject)
    return HttpResponse(resp, content_type='application/json')


def d3_json_logs_specific_day(request, date):
    if not request.user.is_authenticated:
        resp = json.dumps("login!")
        return HttpResponse(resp, content_type='application/json')

    if date is None or len(date) < 8 or len(date) > 8:
        resp = json.dumps("incorrect Date format: YYYYMMDD")
    else:
        year = int(date[:4])
        month = int(date[4:-2])
        day = int(date[6:])
        if (month < 1 or month > 12 or day < 1 or day > 31):
            resp = json.dumps("incorrect Date format: YYYYMMDD")
        else:
            user_date = datetime.datetime(year=year, month=month, day=day, hour=1, minute=1,
                                          second=1, tzinfo=pytz.timezone(request.user.timezone)
                                          )

            proj = request.GET.get('project', None)
            project = Project.objects.filter(name_short=proj)
            test = project.exists() and project.first().developer_allowed(request.user)

            if test:
                data = Timelog.objects.filter(user=request.user,
                                              issue__project__name_short=proj,
                                              created_at__date=user_date.date(),
                                              ).order_by('created_at')

            else:
                data = Timelog.objects.filter(user=request.user,
                                              created_at__date=user_date.date(),
                                              ).order_by('created_at')
            resp = serializers.serialize("json", data)
            resp = json.loads(resp)

            for entry in resp:
                issue_id = entry['fields']['issue']
                iss = Issue.objects.get(id=issue_id)
                entry['fields']['issue_title'] = iss.title
                entry['fields']['issue_short'] = iss.get_ticket_identifier()
                proj = Project.objects.get(id=iss.project.id)
                entry['fields']['issue_project_name'] = proj.name
                entry['fields']['issue_url'] = reverse('issue:detail',
                                                       kwargs={"project": proj.name_short, "sqn_i": iss.number}
                                                       )
                entry['fields']['issue_proj_url'] = reverse('project:detail', kwargs={"project": proj.name_short})

            resp = json.dumps(resp)
    return HttpResponse(resp, content_type='application/json')


def create_activity_data_actions(date_from, date_to, project, result):
    data = json.loads(project.activity)
    if isinstance(data, dict):
        data = []
        project.activity = json.dumps(data)
        project.save()

    while date_to.date() >= date_from.date():
        count = 0
        while(True):
            if not data:
                break
            save = data.pop()
            el = dateutil.parser.parse(save)
            el = timezone.localtime(el)
            if el.date() == date_to.date():
                count += 1
            elif el.date() > date_to.date():
                continue
            else:
                data.append(save)
                break
        temp2 = {}
        temp2["datum"] = str(date_to.date())
        temp2["val"] = count
        result.insert(0, temp2)
        date_to -= timedelta(days=1)
    return result


def create_activity_data_timelogs(date_from, date_to, project, result):
    data = Timelog.objects.filter(issue__project=project, created_at__gt=date_from)
    resp = serializers.serialize("json", data)
    while date_from.date() <= date_to.date():
        temp = 0
        date_data = data.filter(created_at__date=date_from.date())
        for d in date_data:
            temp += d.time.total_seconds()
        temp2 = {}
        temp2["datum"] = str(date_from.date())
        temp2["val"] = temp
        result.append(temp2)
        date_from += timedelta(days=1)
    return result


def get_activity_data_for_project(request):
    proj = request.GET.get('project', None)
    delta = int(request.GET.get('delta', '0'))

    if not proj:
        return HttpResponse(json.dumps("You need to pass a GET Paramter 'project'"), content_type='application/json')

    project = Project.objects.filter(name_short=proj).first()

    if project is None or not project.developer_allowed(request.user):
        return HttpResponse(json.dumps("You're not Member of this Project, or login!"), content_type='application/json')

    result = []

    date_to = timezone.localtime(timezone.now())
    date_to = date_to - timedelta(days=delta)
    date_to.replace(hour=0, minute=0, second=0, microsecond=0)
    date_from = date_to - timedelta(days=30)

    # check if request comes from project list or project detail page, get user preference
    if request.META.get('HTTP_REFERER') is not None and 'detail' in request.META.get('HTTP_REFERER'):
        data = request.user.get_preference('project_detail_chart_type_'+proj, default='timelog')
    else:
        data = request.user.get_preference('project_list_chart_type', default='timelog')

    # create data
    if data == 'timelog':
        result = create_activity_data_timelogs(date_from, date_to, project, result)
    elif data == 'actions':
        result = create_activity_data_actions(date_from, date_to, project, result)

    temp2 = {}
    temp2["data"] = data
    result.insert(0, temp2)
    return HttpResponse(json.dumps(result), content_type='application/json')

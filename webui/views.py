from urllib.parse import urlsplit
from django.http import JsonResponse
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings as _settings


def normalize_rendezvous_server(value, fallback_host):
    raw = (value or "").strip()
    if not raw:
        return fallback_host
    if "://" in raw:
        parsed = urlsplit(raw)
        raw = parsed.netloc or parsed.path
    raw = raw.split("/", 1)[0].strip()
    if "@" in raw:
        raw = raw.rsplit("@", 1)[1]
    return raw or fallback_host


@login_required(login_url='/api/user_action?action=login')
def index(request):
    fallback_host = request.get_host().split(":")[0]
    domain = normalize_rendezvous_server(_settings.ID_SERVER, fallback_host)
    return render(request, 'webui.html', {'domain': domain})

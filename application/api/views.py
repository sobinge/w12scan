from django.views.generic.base import View
import json

from django.http import JsonResponse, HttpRequest, QueryDict
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View

from application.api.models import properly
from application.utils.util import format_convert
from config import AUTH_POST_KEY
from pipeline.elastic import Ips, Domains

# Create your views here.
from pipeline.redis import redis_verify


@method_decorator(csrf_exempt, name="dispatch")
class DemoListView(View):

    def get(self, request):
        return JsonResponse({"test": "11"})

    def post(self, request: HttpRequest):
        print(request.body)
        return JsonResponse({"post": "test"})


@method_decorator(csrf_exempt, name="dispatch")
class AddIpActionView(View):

    def post(self, request: HttpRequest):
        key = request.META.get("HTTP_W12SCAN", None)
        if key != AUTH_POST_KEY:
            return JsonResponse({"status": "400", "msg": "Permission verification failed"})
        data = request.body.decode()
        response = {}
        try:
            ip = json.loads(data)
            dd = Ips(**ip)
            dd.save()
            response["status"] = 200
            response["msg"] = "ok"
        except Exception as e:
            response["status"] = 400
            response["msg"] = str(e)

        return JsonResponse(response)


@method_decorator(csrf_exempt, name="dispatch")
class AddDomainActionView(View):

    def post(self, request: HttpRequest):
        key = request.META.get("HTTP_W12SCAN", None)
        if key != AUTH_POST_KEY:
            return JsonResponse({"status": "400", "msg": "Permission verification failed"})
        data = request.body.decode()
        response = {}
        try:
            ip = json.loads(data)
            dd = Domains(**ip)
            dd.save()
            response["status"] = 200
            response["msg"] = "ok"
        except Exception as e:
            response["status"] = 400
            response["msg"] = str(e)

        return JsonResponse(response)


@method_decorator(csrf_exempt, name="dispatch")
class Proper(View):

    # 获得信息
    def get(self, request):
        id = request.GET.get("id", "")
        try:
            m = properly.objects.get(id=id)
        except:
            m = None
        res = {}
        if m:
            data = {}
            data["desc"] = m.descript
            data["domains"] = m.domains
            data["ips"] = m.ips
            data["name"] = m.name
            data["id"] = m.id
            res["status"] = 200
            res["msg"] = data
        else:
            res["status"] = 400
            res["msg"] = "id don't exist"
        return JsonResponse(res)

    # 创建
    def post(self, request):
        name = request.POST.get("name")
        desc = request.POST.get("desc", "这家伙很懒，描述都不想写")
        ips = request.POST.get("ips")
        domains = request.POST.get("domains")
        properly.objects.create(name=name, descript=desc, ips=ips, domains=domains)
        res = {
            "status": 200,
            "msg": "ok"
        }
        return JsonResponse(res)

    # 更新
    def put(self, request):
        data = QueryDict(request.body)
        id = data.get("id")
        name = data.get("name")
        desc = data.get("desc")
        ips = data.get("ips")
        domains = data.get("domains")
        m = properly.objects.get(id=id)
        m.name = name
        m.descript = desc
        m.ips = ips
        m.domains = domains
        m.save()
        res = {
            "status": 200,
            "msg": "ok"
        }
        return JsonResponse(res)

    # 删除
    def delete(self, request):
        id = request.GET.get("id", "")
        try:
            m = properly.objects.get(id=id)
        except:
            m = None
        res = {}
        if m:
            res["status"] = 200
            res["msg"] = "ok"
            m.delete()
        else:
            res["status"] = 400
            res["msg"] = "id don't exist"
        return JsonResponse(res)


@method_decorator(csrf_exempt, name="dispatch")
class Scan(View):

    # 获得信息
    def get(self, request):
        res = {}
        target = request.GET.get("t", None)
        res["status"] = 400
        res["msg"] = "Target has existed database.({})".format(target)
        if target:
            target = format_convert(target)
            b = redis_verify(target)
            if b:
                res["status"] = 200
                res["msg"] = "ok"
        return JsonResponse(res)

    def post(self, request):
        data = request.body.decode().splitlines()
        all = 0
        success = 0
        for temp in data:
            if not temp:
                continue
            all += 1
            target = format_convert(temp)
            b = redis_verify(target)
            if b:
                success += 1
        res = {
            "status": 200,
            "msg": "All:{0} Success:{1}".format(all, success)
        }
        return JsonResponse(res)
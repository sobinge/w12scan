#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2019/1/28 6:14 PM
# @Author  : w8ay
# @File    : elastic.py
from datetime import datetime

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Date, Integer, Keyword, Text, Document, InnerDoc, Nested, Search
from elasticsearch_dsl.connections import connections

from config import ELASTICSEARCH_HOSTS

connections.create_connection(hosts=ELASTICSEARCH_HOSTS)
es = Elasticsearch(ELASTICSEARCH_HOSTS)


class Location(InnerDoc):
    country_id = Keyword()
    country = Keyword()
    region = Keyword()


class Info(InnerDoc):
    extrainfo = Text()
    name = Keyword()
    prot = Integer()
    product = Text()
    version = Keyword()


class Ips(Document):
    location = Nested(Location)
    infos = Nested(Info)
    target = Keyword()
    published_from = Date()

    class Index:
        name = 'w12scan'
        settings = {
            "number_of_shards": 2,
        }

    class Meta:
        doc_type = 'ips'

    def save(self, **kwargs):
        if not self.published_from:
            self.published_from = datetime.now()
        return super().save(**kwargs)


class Domains(Document):
    status_code = Integer()
    title = Text()
    headers = Text()
    body = Text()
    Server = Text()
    ip = Keyword()
    url = Keyword()
    CMS = Keyword()
    published_from = Date()

    class Index:
        name = 'w12scan'
        settings = {
            "number_of_shards": 2,
        }

    class Meta:
        doc_type = 'domains'

    def save(self, **kwargs):
        if not self.published_from:
            self.published_from = datetime.now()
        return super().save(**kwargs)


def es_search_ip(ip):
    _q = {

        "query": {
            "match": {
                "target": ip
            }
        }

    }
    s = Search(using=es, index='w12scan', doc_type="ips").from_dict(_q)
    if s.count() > 0:
        return list(s)[0]
    return False


def es_search_ip_by_id(id):
    _q = {

        "query": {
            "match": {
                "_id": id
            }
        }

    }
    s = Search(using=es, index='w12scan').from_dict(_q)
    dd = s.execute().to_dict().get("hits")
    if dd:
        dd = dd.get("hits")
    else:
        return False
    return dd


def es_search_domain_by_ip(ip):
    payload = {
        "query": {
            "match": {
                "ip": ip
            }
        }
    }
    s = Search(using=es, index='w12scan', doc_type='domains').from_dict(payload)
    res = s.execute()
    union_domains = []
    for hit in res:
        cid = hit.meta.id
        d = hit.to_dict()
        domain = d["url"]
        title = d.get("title", "")
        union_domains.append({"id": cid, "url": domain, "title": title})
    return union_domains


def count_app():
    payload = {
        "size": 0,
        "aggs": {
            "genres": {
                "terms": {
                    "field": "app.keyword",
                    "size": 8
                }
            }
        }
    }
    s = Search(using=es, index='w12scan', doc_type="domains").from_dict(payload)
    res = s.execute().to_dict()
    try:
        r = res["aggregations"]["genres"]["buckets"]
    except KeyError:
        r = None
    return r


def count_country():
    payload = {"size": 0,
               "aggs": {
                   "location": {
                       "nested": {
                           "path": "location"
                       },
                       "aggs": {
                           "country": {
                               "terms": {
                                   "field": "location.country_id"
                               }
                           }
                       }
                   }
               }
               }
    s = Search(using=es, index='w12scan', doc_type='ips').from_dict(payload)
    res = s.execute().to_dict()
    try:
        r = res["aggregations"]["location"]["country"]["buckets"]
    except KeyError:
        r = None
    return r


def count_name():
    payload = {"size": 0,
               "aggs": {
                   "infos": {
                       "nested": {
                           "path": "infos"
                       },
                       "aggs": {
                           "name": {
                               "terms": {
                                   "field": "infos.name"
                               }
                           }
                       }
                   }
               }
               }
    s = Search(using=es, index='w12scan', doc_type='ips').from_dict(payload)
    res = s.execute().to_dict()
    try:
        r = res["aggregations"]["infos"]["name"]["buckets"]
    except KeyError:
        r = None
    return r


def count_port():
    payload = {"size": 0,
               "aggs": {
                   "infos": {
                       "nested": {
                           "path": "infos"
                       },
                       "aggs": {
                           "port": {
                               "terms": {
                                   "field": "infos.port"
                               }
                           }
                       }
                   }
               }
               }
    s = Search(using=es, index='w12scan', doc_type='ips').from_dict(payload)
    res = s.execute().to_dict()
    try:
        r = res["aggregations"]["infos"]["port"]["buckets"]
    except KeyError:
        r = None
    return r


def total_data():
    ips = Search(using=es, index='w12scan', doc_type='ips')
    domains = Search(using=es, index='w12scan', doc_type='domains')
    return ips.count(), domains.count()


def total_bug():
    payload = {"query": {"exists": {"field": "bugs"}
                         }, "size": 0
               }
    s = Search(using=es, index='w12scan').from_dict(payload)
    res = s.execute().to_dict()
    return res["hits"]["total"]


if __name__ == '__main__':
    Ips.init()
    Domains.init()
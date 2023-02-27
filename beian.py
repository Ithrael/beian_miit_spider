#!/usr/bin/env python3
import os
import urllib3
from urllib import parse
import requests
import argparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DESCRIPTION='''
beian_miit_spider 
Query domain name [put on record] script.
'''
DEFAULT_OUT = "domains.txt"
DEFAULT_MODE="f"
argv:None

class Beian(object):
    timeout = 30
    url = "https://m-beian.miit.gov.cn/webrec/queryRec"
    header = {
        "Host": "m-beian.miit.gov.cn",
        "Origin": "https://m-beian.miit.gov.cn",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Referer": "https://m-beian.miit.gov.cn/",
        "Accept-Language": "zh-cn",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "Content-Type": "application/x-www-form-urlencoded",
        "Connection": "keep-alive"
    }

    def __init__(self, comp, proxy={'http': 'http://localhost:8080'}):
        self.comp = comp
        self.proxies = proxy
        self.encode_comp = parse.quote(comp, encoding='utf-8')
        self.domains = []

    def query_host_by_comp(self):
        param = "keyword={}&pageIndex=1&pageSize=20".format(self.encode_comp)

        with requests.post(self.url, data=param, headers=self.header, proxies=self.proxies, timeout=self.timeout,
                           verify=False) as r:
            if r.status_code != 200:
                return
            res_json = r.json()
            total_page = res_json["result"]["totalPages"]
            content = res_json["result"]["content"]
            if not content:
                return
            for item in content:
                domain = item["domain"]
                self.domains.append(domain)
            for page in range(2, int(total_page) + 1):
                self.query_host_by_comp_page(page)

    def query_host_by_comp_page(self, page):
        param = "keyword={}&pageIndex={}&pageSize=20".format(self.encode_comp, page)

        with requests.post(self.url, data=param, headers=self.header, proxies=self.proxies, timeout=self.timeout,
                           verify=False) as r:
            if r.status_code != 200:
                return
            res_json = r.json()
            content = res_json["result"]["content"]
            if not content:
                return
            for item in content:
                domain = item["domain"]
                self.domains.append(domain)

    def query_comp_by_host(self):
        param = "keyword={}&pageIndex=1&pageSize=20".format(self.encode_comp)

        with requests.post(self.url, data=param, headers=self.header, proxies=self.proxies, timeout=self.timeout,
                           verify=False) as r:
            if r.status_code != 200:
                return
            res_json = r.json()
            content = res_json["result"]["content"]
            if not content:
                return
            for item in content:
                serviceName = item["serviceName"]
                self.domains.append(serviceName)


def query_host(host):
    beian = Beian(host)
    beian.query_comp_by_host()
    print("\n".join(beian.domains))
    return beian.domains


def query(comp):
    beian = Beian(comp)
    beian.query_host_by_comp()
    print("\n".join(beian.domains))
    return beian.domains


def query_file(comp_f_path):
    if not os.path.exists(comp_f_path):
        raise FileNotFoundError('the file is not found: {}'.format(comp_f_path))
    domains = []
    for comp in open(comp_f_path, 'r', encoding='utf-8').readlines():
        beian = Beian(comp.strip())
        beian.query_host_by_comp()
        domains = beian.domains
        print(comp)
        print("\n".join(domains))
        domains.extend(domains)
    return domains


def init_command_args():
    """
    初始化运行参数
    """
    #换了一个参数接收方式
    parser=argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("--comp",type=str,help="query comp name")
    parser.add_argument("-mode",type=str,choices=['c','f','h'],default=DEFAULT_MODE,help="query mode: c for comp, f for file, h for host, default: {}".format(DEFAULT_MODE))
    parser.add_argument("--file",type=str,help="query comp file path")
    parser.add_argument("--host",type=str,help="query host")
    parser.add_argument("--out",type=str,default=DEFAULT_OUT,help="output file, default:{}".format(DEFAULT_OUT))
    global argv
    argv=parser.parse_args()

def main():
    res = []
    mode = argv.mode
    out=argv.out
    if mode == 'c' and argv.comp:
        res = query(argv.comp)
    elif mode == 'f' and argv.file:
        res = query_file(argv.file)
    elif mode == 'h' and argv.host:
        res = query_host(argv.host)
    else:
        print("Required parameters are not available, the script exits.")
        exit(0)

    with open(out, 'w', encoding='utf-8') as writer:
        writer.write("\n".join(res))
    print("over!")


if __name__ == '__main__':
    init_command_args()
    main()

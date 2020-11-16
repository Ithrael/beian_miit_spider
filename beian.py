import os
import urllib3
from urllib import parse
import requests
from absl import app, flags

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FLAGS = flags.FLAGS
DEFAULT_COMP = "中国铁路上海局集团有限公司"
DEFAULT_OUT = "domains.txt"


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

    def __init__(self, comp, proxy=None):
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
    flags.DEFINE_string('comp', DEFAULT_COMP, 'query comp name, default: {}'.format(DEFAULT_COMP))
    flags.DEFINE_string('mode', 'comp', 'query mode: comp or file, default: comp')
    flags.DEFINE_string('comp_f_path', '', 'query comp file path, default: None')
    flags.DEFINE_string('out', DEFAULT_OUT, 'output file, default: {}'.format(DEFAULT_OUT))


def main(_):
    res = []
    out = FLAGS.out
    if FLAGS.mode == 'comp':
        comp = FLAGS.comp
        res = query(comp)
    elif FLAGS.mode == 'file':
        comp_f_path = FLAGS.comp_f_path
        res = query_file(comp_f_path)

    with open(out, 'w', encoding='utf-8') as writer:
        writer.write("\n".join(res))
    print("over!")


if __name__ == '__main__':
    init_command_args()
    app.run(main)

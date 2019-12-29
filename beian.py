import re
import time
import sys
import base64
import random
from urllib import parse
import requests
from bs4 import BeautifulSoup


class Beian(object):
    index_url = "http://beian.miit.gov.cn/publish/query/indexFirst.action"
    # 验证码接口，各位大佬手下留情，不要hack
    verify_url = "http://123.207.50.164:5000/captcha/v1"
    index_header = {
        "Host": "beian.miit.gov.cn",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.87 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive"
    }

    header = {
        "Host": "beian.miit.gov.cn",
        "Origin": "http://beian.miit.gov.cn",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.87 Safari/537.36",
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
        "Referer": "http://beian.miit.gov.cn/icp/publish/query/icpMemoInfo_showPage.action",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cookie": "Hm_lvt_af6f1f256bb28e610b1fc64e6b1a7613=1572332410,1572946370; __jsluid_h=3f6bd229dea89287a7ad3394cdc501ca; JSESSIONID=-adGSUifF9D5BSas1h2nrWGAsOV9pCX7UXq1lVDU0lnnWcEp2USC!-652379638",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive"
    }

    query_header = {
        "Host": "beian.miit.gov.cn",
        "Content-Length": "209",
        "Cache-Control": "max-age=0",
        "Origin": "http://beian.miit.gov.cn",
        "Upgrade-Insecure-Requests": "1",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.87 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "http://beian.miit.gov.cn/icp/publish/query/icpMemoInfo_showPage.action",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cookie": "JSESSIONID=dedR-mryRZv5PUE7RNeOl-pPTadKUF_KHQcTPnglmgQ8ADP7uj7S!1834962369; __jsluid_h=03db969a2215a3f2eb4d9276f24bc35f",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive"
    }

    def __init__(self, comp, proxy=None):
        self.cookie = ""
        self.img_content = ""
        self.code = ""
        self.comp = comp
        self.proxies = proxy
        self.websites = []

    def get_cookie(self):
        try:
            with requests.get(self.index_url, headers=self.index_header, timeout=5, proxies=self.proxies, verify=False) as r:
                if r.status_code != 200:
                    return
                response_header = r.headers
                JSESSIONID = "".join(re.findall("JSESSIONID.*?;", str(response_header)))
                __jsluid_h = "".join(re.findall("__jsluid_h.*?;", str(response_header)))
                cookie = " ".join([JSESSIONID, __jsluid_h])
                self.cookie = cookie
        except Exception as e:
            print(e)
            self.get_cookie()

    def mark_code(self):
        image = base64.b64encode(self.img_content).decode('utf-8')
        with requests.post(url=self.verify_url, json={'image': image}, timeout=5) as r:
            self.code = r.json().get('message', "")

    def get_verify_img(self):
        url = "http://beian.miit.gov.cn/getVerifyCode?"+str(random.randint(10, 99))
        self.header["Cookie"] = self.cookie
        with requests.get(url, headers=self.header, timeout=10, proxies=self.proxies, verify=False) as r:
            self.img_content = r.content

    def vilidCode(self):
        url = "http://beian.miit.gov.cn/common/validate/validCode.action"
        param = {
            "validateValue": self.code
        }
        with requests.post(url, data=param, headers=self.header, proxies=self.proxies, timeout=5, verify=False) as r:
            if r.status_code != 200:
                return False
            if "true" in r.text:
                return True
            return False

    def verify_code(self):
        self.get_verify_img()
        self.mark_code()

    def req_host_by_comp(self):
        self.query_header["Cookie"] = self.cookie
        url = "http://beian.miit.gov.cn/icp/publish/query/icpMemoInfo_searchExecute.action"

        encode_comp = parse.quote(comp, encoding='gbk')
        param = "siteName=&siteDomain=&siteUrl=&mainLicense=&siteIp=&condition=5&unitName={}+" \
                "&mainUnitNature=-1&certType=-1&mainUnitCertNo=&verifyCode={}".format(encode_comp, self.code)

        with requests.post(url, data=param, headers=self.query_header, proxies=self.proxies, timeout=5, verify=False) as r:
            if r.status_code != 200:
                return
            html = r.text
            page = "".join(re.findall("当前第&nbsp;1/(\\d+)&nbsp;页", html, re.S))
            soup = BeautifulSoup(html, "lxml")
            items = soup.select("td.bxy > div > a")
            for item in items:
                self.websites.append(item.text)
            if page.strip() == "":
                return
            for i in range(2, int(page)+1):
                self.req_host_by_comp_page(str(i))

    def req_host_by_comp_page(self, page):
        self.query_header["Referer"] = "http://beian.miit.gov.cn/icp/publish/query/icpMemoInfo_searchExecute.action"
        url = "http://beian.miit.gov.cn/icp/publish/query/icpMemoInfo_searchExecute.action"

        while 1:
            self.verify_code()
            if self.vilidCode() and len(self.code) == 6:
                break
            time.sleep(1)

        encode_comp = parse.quote(comp, encoding='gbk')

        param = "unitName={}&siteName=&siteDomain=&siteUrl=&mainLicense=&siteIp=&mainUnitNature=-1&" \
                "certType=-1&mainUnitCertNo=&" \
                "page.pageSize=20&pageNo={}&jumpPageNo=&verifyCode={}".format(encode_comp, page, self.code)
        with requests.post(url, data=param, headers=self.query_header, proxies=self.proxies, timeout=5, verify=False) as r:
            if r.status_code != 200:
                return
            html = r.text
            soup = BeautifulSoup(html, "lxml")
            items = soup.select("td.bxy > div > a")

            if "没有符合条件的记录" not in html and len(items) == 0:
                self.req_host_by_comp_page(page)
            for item in items:
                self.websites.append(item.text)


def query(comp):
    beian = Beian(comp)
    beian.get_cookie()

    while 1:
        beian.verify_code()
        print(beian.code, beian.vilidCode())

        if beian.vilidCode() and len(beian.code) == 6:
            break
        time.sleep(1)

    beian.req_host_by_comp()
    return beian.websites


if __name__ == '__main__':
    # comp = "北京三快科技有限公司"
    comp = sys.argv[1]
    print(comp)
    websites = query(comp)
    print(websites)




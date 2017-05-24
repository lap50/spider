import requests
import re
from shopvisit.random_header import RandomHeader
from lxml import html
import threading
from time import ctime,sleep
from shopvisit_model import ShopvisitModel
import random


category_urls = [
    "https://www.tmall.com/wow/chaoshi/act/catpopup?wh_id=jksp&wh_logica=HD",
    "https://www.tmall.com/wow/chaoshi/act/catpopup?wh_id=spyl&wh_logica=HD",
    "https://www.tmall.com/wow/chaoshi/act/catpopup?wh_id=lyfs&wh_logica=HD",
    "https://www.tmall.com/wow/chaoshi/act/catpopup?wh_id=mrxh&wh_logica=HD",
    "https://www.tmall.com/wow/chaoshi/act/catpopup?wh_id=jjjd&wh_logica=HD",
    "https://www.tmall.com/wow/chaoshi/act/catpopup?wh_id=jtqj&wh_logica=HD",
    "https://www.tmall.com/wow/chaoshi/act/catpopup?wh_id=myyp&wh_logica=HD",
    "https://www.tmall.com/wow/chaoshi/act/category?wh_logica=HD"
]

def start_requests(category_url):
    randomHeader = RandomHeader()
    ip = randomHeader.random_ip()
    ua = randomHeader.random_ua()

    session = requests.session()
    headers = {}
    headers['User-Agent'] = ua
    headers['Host'] = 'www.tmall.com'
    proxies = {"https": "http://" + ip}
    list_urls = []
    r = session.get(category_url, headers=headers, proxies=proxies)
    list_data = r.json()
    # print(list_data)
    # 遍历分类url地址
    if "catpopup" in category_url:
        for cate_url in list_data['data']['cats']:
            # print(cate_url['title'] + ":" + cate_url['link'])
            list_urls.append("https:" + cate_url['link'])
    elif "category" in category_url:
        for cate_url in list_data['data']:
            if cate_url['name'] == "生鲜水果":
                for recommend in cate_url['recommends']:
                    # print(recommend['name']+":"+"https:" + recommend['link'])
                    list_urls.append("https:" + recommend['link'])
    return list_urls


def parse(list_url):
    randomHeader = RandomHeader()
    ip = randomHeader.random_ip()
    ua = randomHeader.random_ua()

    session = requests.session()

    headers = {
        'User-Agent':ua,
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate, br',
        'Accept-Language':'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Connection':'keep-alive',
        'Referer':'https://chaoshi.tmall.com/',
        'Upgrade-Insecure-Requests':'1',
    }
    proxies = {"https": "http://" + ip}

    # 每个列表页会进行几次跳转，获取到cookie
    headers['Host'] = 'list.tmall.com'
    res = session.get(list_url, headers=headers, allow_redirects=False, proxies=proxies)
    # res = session.get(list_url, headers=headers, allow_redirects=False)
    # sleep(1)
    headers['Host'] = 'login.taobao.com'
    res = session.get(res.headers['Location'], headers=headers, allow_redirects=False, proxies=proxies)
    # res = session.get(res.headers['Location'], headers=headers, allow_redirects=False)
    # sleep(1)
    headers['Host'] = 'pass.tmall.com'
    res = session.get(res.headers['Location'], headers=headers, allow_redirects=False, proxies=proxies)
    # res = session.get(res.headers['Location'], headers=headers, allow_redirects=False)
    cookies = res.cookies
    # sleep(1)
    headers['Host'] = 'list.tmall.com'
    res = session.get(res.headers['Location'], headers=headers, cookies=cookies, allow_redirects=False, proxies=proxies)
    # res = session.get(res.headers['Location'], headers=headers, cookies=cookies, allow_redirects=False)
    # sleep(1)
    parse_product(session, res.headers['Location'], headers, cookies, proxies)
    from_url = res.headers['Location']
    # res = session.get(res.headers['Location'], headers=headers, cookies=cookies, allow_redirects=False, proxies=proxies)
    # res = session.get(res.headers['Location'], headers=headers, cookies=cookies, allow_redirects=False)
    # print(res.content)
    # cookies = dict(cookies)
    # print(cookies)

def parse_product(session, url, header, cookie, proxy = '', from_url = ''):
    shopvisitModel = ShopvisitModel()
    if not from_url.strip():
        header['Referer'] = from_url
    res = session.get(url, headers=header, cookies=cookie, allow_redirects=False, proxies=proxy)
    # res = session.get(url, headers=header, cookies=cookie, allow_redirects=False)
    # print(res.content)
    tree = html.fromstring(res.text)
    item_nodes = tree.xpath("//div[@class='mainItemsList']//li[@data-itemid]")
    # print(item_nodes)

    # 得到商品数据
    item = {}
    for each in item_nodes:
        url = each.xpath(".//h3/a/@href")[0]
        item['product_id'] = re.search("id=(\d+)", url).group(1)
        product_name = each.xpath(".//h3/a/text()")
        product_name = product_name[0].replace('\n', '').replace(' ', '')
        if "【天猫超市】" in product_name:
            item['product_name'] = product_name.replace('【天猫超市】', '')
        else:
            item['product_name'] = product_name
        try:
            item['buy_num'] = each.xpath(".//div[@class='item-sum']/strong/text()")[0]
        except:
            item['buy_num'] = 0
        item['price'] = each.xpath(".//span[@class='ui-price']/strong/text()")[0]
        item['plat'] = 'tm'
        item['detail'] = ''
        item['from_url'] = url
        # print(item)
        insert_res = shopvisitModel.insert_item(item)
        # print(insert_res)
    secs = [15,16,17,18,19,20]
    sec = random.choice(secs)
    sleep(sec)
    # 翻页
    page_next_node = tree.xpath("//a[@class='page-next']/@href")[0]
    # print(page_next_node)
    page_next_url = "https://list.tmall.com/search_product.htm" + page_next_node
    parse_product(session, page_next_url, header, cookie, proxy, url)
    # res = session.get(page_next_url, headers=headers, cookies=cookies, allow_redirects=False)
    # print(res.text)


# 获取二级分类列表地址
list_urls = start_requests(random.choice(category_urls))
# print(list_urls)

# parse(list_urls[0])
# 多线程执行
if len(list_urls) > 0:
    threads = []
    for list_url in list_urls:
        t = threading.Thread(target=parse,args=(list_url,))
        t.setDaemon(True)
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()
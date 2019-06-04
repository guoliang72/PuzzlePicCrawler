from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import re
import processer
import time
import redis
import pymongo
import json

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["crawler"]
urls_model = mydb["urls"]

cli = redis.Redis(db=2)

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')

def download_search_page(url):
	browser = webdriver.Chrome(options=chrome_options)
	browser.get(url)
	ele = browser.find_element_by_css_selector("body")
	scroll_times = 100
	while scroll_times:
		try:
			more = browser.find_element_by_css_selector('a.btn_seemore.cbtn.mBtn')
			more.click()
			break
		except Exception:
			ele.send_keys(Keys.END)
			time.sleep(0.5)
		scroll_times -= 1
	scroll_times = 50
	while scroll_times:
		ele.send_keys(Keys.END)
		time.sleep(0.5)
		scroll_times -= 1
	html_text = str(browser.page_source)

	suggests_urls = []
	try:
		suggests = browser.find_elements_by_css_selector('a.suggestion-item')
		suggests_urls = [s.get_attribute('href') for s in suggests]
	except Exception as e:
		pass

	browser.quit()
	return html_text, suggests_urls

def get_images_url(html_text):
	soup = BeautifulSoup(html_text,'lxml')
	eles = soup.select('a.iusc')
	urls = []
	pat =  re.compile('"murl":"(.*?.jpg)","turl"')
	for e in eles:
		urls.extend(pat.findall(str(e)))
	return urls

def run(pid):
	url = cli.lindex('crawler:search:url_list', -1)
	if not url:
		return False
	try:
		url = str(url,encoding='utf-8')
		pat = re.compile('q=(.*?)&')
		word = pat.findall(url)[0]
		word = ''.join(re.findall('\w', word))
		print('pid: %d, %s start' % (pid, word))
		html_text, suggests_urls = download_search_page(url)
		urls = get_images_url(html_text)
		urls_model.insert_one({
			'word': word,
			'site_url': url,
			'image_urls': urls,
			'suggests_urls': suggests_urls
		})
		print('pid: %d, %s, image_urls: %d, suggests_urls: %d' % (pid, word, len(urls), len(suggests_urls)))
		for surl in suggests_urls:
			if cli.sadd('crawler:search:url_set', surl):
				cli.lpush('crawler:search:url_list', surl)
	except Exception as e:
		print(e)
	cli.rpop('crawler:search:url_list')
	return True

if __name__ == '__main__':
	while run(0):
		continue

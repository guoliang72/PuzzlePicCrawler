from bs4 import BeautifulSoup
from selenium import webdriver
import requests
import re
import processer

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')

def download_search_page(url):
	browser = webdriver.Chrome(options=chrome_options)
	browser.get(url)
	ret = str(browser.page_source)
	browser.quit()
	return ret

def load_downloaded_page(path):
	with open(path) as f:
		return f.read()

def get_images_url(html_text):
	soup = BeautifulSoup(html_text,'lxml')
	eles = soup.select('a.iusc')
	urls = []
	pat =  re.compile('"murl":"(.*?.jpg)","turl"')
	for e in eles:
		urls.extend(pat.findall(str(e)))
	return urls


def download_images(urls, keyword):
	for i, url in enumerate(urls):
		print("start download %s" % url)
		try:
			image_name = "%s_%d.jpg" % (keyword, i)
			image_path = "raw_images/%s" % image_name
			html = requests.get(url, timeout=5)
			with open(image_path,"wb")as f:
			    f.write(html.content)
			print("%s of total %d downloaded\n" % (image_name, len(urls)))
			processer.process(image_path, image_name)
		except Exception as e:
			print("%s download failed\n" % image_name, e)

def run(keyword):
	print("\n", "-"*10, keyword)
	url = r'https://www.bing.com/images/search?q=' + keyword + r'&first=1&count=100&qft=+filterui%3aimagesize-custom_640_640&FORM=IRMHRE'
	html_text = download_search_page(url)
	with open('tmp.html', 'w') as f:
		f.write(html_text)
	urls = get_images_url(html_text)
	with open('urls.txt', 'a') as urls_file:
		urls_file.write('\n'.join(urls))
		urls_file.write('\n')
	print(urls)
	download_images(urls, keyword)

if __name__ == '__main__':
	keyword = 'dog'
	url = r'https://www.bing.com/images/search?q=' + keyword + r'&first=1&count=100&qft=+filterui%3aimagesize-custom_640_640&FORM=IRMHRE'
	html_text = download_search_page(url)
	with open('tmp.html', 'w') as f:
		f.write(html_text)
	#path = 'tmp.html'
	#html_text = load_downloaded_page(path)
	urls = get_images_url(html_text)
	print(urls)
	#download_images(urls, keyword)

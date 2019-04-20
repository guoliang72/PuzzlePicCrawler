from bs4 import BeautifulSoup
import requests
import re
import processer

keyword = "sport"

def download_search_page(url):
	r=requests.get(url, timeout=30)#请求超时时间为30秒
	r.raise_for_status()#如果状态不是200，则引发异常
	r.encoding=r.apparent_encoding #配置编码
	return r.text

def load_downloaded_page(path):
	with open(path) as f:
		return f.read()

def get_images_url(html_text):
	soup = BeautifulSoup(html_text,'lxml')
	eles = soup.select('a.iusc')
	urls = []
	pat =  re.compile('"murl":"(.*)","turl"')
	for e in eles:
		urls.extend(pat.findall(str(e)))
	return urls

def download_images(urls):
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

if __name__ == '__main__':
	#url = r'https://cn.bing.com/images/search?q=indoor&qft=+filterui:imagesize-custom_640_640+filterui:license-L2_L3_L4_L5_L6_L7'
	#html_text = download_search_page(url)
	path = 'tmp.html'
	html_text = load_downloaded_page(path)
	urls = get_images_url(html_text)
	download_images(urls)

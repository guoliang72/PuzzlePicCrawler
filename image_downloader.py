import pymongo
import redis
import processer
import requests
import os
import multiprocessing

def download_image(url, keyword, idx):
	#print("start download %s" % url)
	try:
		image_name = "%s_%d.jpg" % (keyword, idx)
		image_path = "raw_images/%s" % image_name
		html = requests.get(url, timeout=5)
		with open(image_path,"wb")as f:
			f.write(html.content)
		processer.process(image_path, image_name)
		if os.path.exists(image_path):
			os.remove(image_path)
	except Exception:
		print("%s download failed\n" % image_name)

def worker(pid):
	cli = redis.Redis(db=2)
	myclient = pymongo.MongoClient("mongodb://localhost:27017/")
	db = myclient["crawler"]

	urls = list(db.urls.find())
	for url in urls:
		word, img_urls = url['word'], url['image_urls']
		if not cli.sadd('crawler:process:url_set', word):
			continue
		print(pid, 'start process %d images of word %s' % (len(img_urls), word))
		for i, img_url in enumerate(img_urls):
			download_image(img_url, word, i)
		print(pid, 'end process word %s, total process %d images' % (word, len(img_urls)))

if __name__ == '__main__':
	pool = multiprocessing.Pool(4)
	pool.map(worker, [i for i in range(4)])
import downloader

def worker(pid):
	while downloader.run(pid):
		pass

def start_crawler():
	from multiprocessing import Pool
	pool = Pool()
	pool.map(worker, [i for i in range(4)])

def parse_toefl(path):
	import redis
	cli = redis.Redis(db=2)
	with open(path) as f:
		lines = f.readlines()
		for i in range(0, len(lines)):
			args = lines[i].strip().split()
			word = args[0]
			url = r'https://www.bing.com/images/search?q=' + word + r'&first=1&count=100&qft=+filterui%3aimagesize-custom_640_640&FORM=IRMHRE'
			if cli.sadd('crawler:search:url_set', url):
				cli.lpush('crawler:search:url_list', url)
			'''
			try:
				print('start %d %s' % (i, word))
				downloader.run(word)
			except Exception as e:
				print('failed at %d %s' % (i, word))
			'''

if __name__ == '__main__':
	parse_toefl('TOEFL.txt')
	#start_crawler()
import requests
import processer

def parse_url_file(filepath):
	with open(filepath) as f:
		while True:
			try:
				l = f.readline()
				args = l.strip().split()
				if len(args) != 2:
					continue
				name, url = args
				if not url.endswith('.jpg'):
					continue
				yield name, url
			except UnicodeDecodeError as e:
				continue
			except EOFError:
				break

def download_images(filepath):
	process_count = 0
	for name, url in parse_url_file(filepath):
		print("start download %s from %s" % (name, url))
		try:
			image_name = "%s.jpg" % name
			image_path = "raw_images/%s" % image_name
			html = requests.get(url, timeout=5)
			with open(image_path,"wb")as f:
			    f.write(html.content)
			processer.process(image_path, image_name)
		except Exception as e:
			print("%s download failed\n" % image_name, e)
		finally:
			process_count += 1
			print(process_count, "-" * 10, "\n")
			if process_count > 100:
				break

if __name__ == '__main__':
	download_images('images_dataset/image_urls')

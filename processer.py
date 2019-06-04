import cv2 as cv
import numpy as np
import os
import requests
import redis

cli = redis.Redis(db=2)

def check_mean_std_dev(img):
	h, w = img.shape[:2]
	for i in range(2):
		for j in range(2):
			sub_img = img[int(i*h/2):int((i+1)*h/2), int(j*w/2):int((j+1)*w/2)]
			_, std_dev = cv.meanStdDev(sub_img)
			#print(std_dev)
			if max(std_dev) < 50:
				return False
	sub_img = img[int(0.5*h/2):int(1.5*h/2), int(0.5*w/2):int(1.5*w/2)]
	_, std_dev = cv.meanStdDev(sub_img)
	#print(std_dev)
	if max(std_dev) < 50:
		return False
	_, std_dev = cv.meanStdDev(img)
	#print(std_dev)
	if max(std_dev) < 50:
		return False
	return True

def check_sub_img_similar(img):
	h, w, _ = img.shape
	
	i1, i2 = img[:int(h/2), :, :], img[int(h/2):, :, :]
	h1, _ = np.histogram(i1, bins=128)
	h2, _ = np.histogram(i2, bins=128)
	h1, h2 = np.float32(h1), np.float32(h2)
	m = cv.compareHist(h1, h2, cv.HISTCMP_CORREL)
	#print(m)
	if m > 0.9:
		return False

	i1, i2 = img[:, :int(w/2), :], img[:, int(w/2):, :]
	h1, _ = np.histogram(i1, bins=128)
	h2, _ = np.histogram(i2, bins=128)
	h1, h2 = np.float32(h1), np.float32(h2)
	m = cv.compareHist(h1, h2, cv.HISTCMP_CORREL)
	#print(m)
	if m > 0.9:
		return False
	return True

def edge(img, img_name):
	#定义结构元素
	kernel = cv.getStructuringElement(cv.MORPH_RECT,(11, 11))
	#闭运算
	closed = cv.morphologyEx(img, cv.MORPH_CLOSE, kernel)
	#cv.imwrite('closed/%s' % img_name, closed)
	#开运算
	opened = cv.morphologyEx(img, cv.MORPH_OPEN, kernel)
	#cv.imwrite('opened/%s' % img_name, opened)
	#高斯模糊,降低噪声
	blurred = cv.GaussianBlur(opened,(3,3),1)
	#灰度图像
	gray=cv.cvtColor(blurred,cv.COLOR_RGB2GRAY)
	#图像梯度
	xgrad=cv.Sobel(gray,cv.CV_16SC1,1,0)
	ygrad=cv.Sobel(gray,cv.CV_16SC1,0,1)
	#计算边缘
	#50和150参数必须符合1：3或者1：2
	edge_output=cv.Canny(xgrad,ygrad,50,150)
	dst=cv.bitwise_and(gray,gray,mask=edge_output)
	return dst, closed

def get_square(img):
	h, w = img.shape[:2]
	tile = 64
	dp = [[0 for _ in range(w)] for _ in range(h)]
	bg = [[0 for _ in range(w)] for _ in range(h)]
	for i in range(h):
		row_sum = 0
		bg_row_sum = 0
		for j in range(w):
			row_sum += 1 if img[i][j] else 0
			dp[i][j] = (dp[i-1][j] if i else 0) + row_sum

	for i in range(h-640+tile):
		for j in range(w-640+tile):
			sum_arr = []
			filled = True
			for ti in range(i, i + 640 - tile, tile):
				sum_arr.append([])
				for tj in range(j, j + 640 - tile, tile):
					square_sum = dp[ti+tile][tj+tile] - dp[ti+tile][tj] - dp[ti][tj+tile] + dp[ti][tj]
					sum_arr[-1].append(square_sum)
					if square_sum < 1:
						filled = False
						break
				if not filled:
					break
			if filled:
				#print(sum_arr)
				return i, j

	return -1, -1

def generate_thumb(img):
	return cv.resize(img, (0, 0), fx=0.25, fy=0.25, interpolation=cv.INTER_NEAREST)

def resize(img):
	h, w = img.shape[:2]
	ratio = 650 / w if h > w else 650 / h
	return cv.resize(img, (0, 0), fx=ratio, fy=ratio, interpolation=cv.INTER_NEAREST)

def save_img(img, img_name):
	word, idx = img_name[:-4].split('_')
	filename = "%s%s_10x10.jpg" % (word, idx)
	thumb = generate_thumb(img)
	thumbname = "%s%s_10x10_thumb.jpg" % (word, idx)
	cv.imwrite('/Users/weiyuhan/git/CrowdJigsaw/public/images/raw/%s' % filename, img)
	cv.imwrite('/Users/weiyuhan/git/CrowdJigsaw/public/images/raw/%s' % thumbname, thumb)
	print('save %s to CrowdJigsaw' % filename)

def process(img_path, img_name):
	img = cv.imread(img_path)
	if img is None:
		return
	h, w = img.shape[:2]
	#print(h, w)
	if h < 650 and w < 650:
		return
	resize_img = resize(img)
	#cv.imwrite('resize/%s' % img_name, resize_img)
	gray, closed = edge(resize_img, img_name)
	#cv.imwrite('gray/%s' % img_name, gray)
	si, sj = get_square(gray)
	if si >= 0 and sj >= 0:
		cropped_closed = closed[si:si+640, sj:sj+640]
		if check_mean_std_dev(cropped_closed) and check_sub_img_similar(cropped_closed):
			cropped = resize_img[si:si+640, sj:sj+640]
			print('writing %s from (%d, %d)' % (img_name, si, sj))
			cv.imwrite('images/%s' % img_name, cropped)
			save_img(cropped, img_name)


def process_images(path):
	work_dir = path
	for parent, dirnames, filenames in os.walk(work_dir,  followlinks=True):
		#print(filenames)
		for filename in filenames:
			if not filename.endswith(".jpg") and not filename.endswith(".JPEG"):
				continue
			file_path = os.path.join(parent, filename)
			print('process %s' % filename)
			try:
				process(file_path, filename)
			except Exception as e:
				print(e)

def run(pid):
	search_url = cli.lpop('crawler:image:url_list')
	if not search_url:
		return False
	url = str(url,encoding='utf-8')
	pat = re.compile('q=(.*?)&')
	word = pat.findall(url)[0]
	word = ''.join(re.findall('\w', word))
	idx = 50
	while True:
		image_url = cli.lpop('crawler:image:url_list:' + word)
		if not image_url:
			break
		cli.srem('crawler:image:url_set:' + word, image_url)
		download_images(image_url, word, idx)
		idx += 1
	cli.srem('crawler:search:url_set', url)

if __name__ == '__main__':
	run(0)
	'''
	for img_name in ['abstraction_15.jpg', 'apex_15.jpg']:
		print(img_name)
		file_path = 'raw_images/%s' % img_name
		process(file_path, img_name)
	'''
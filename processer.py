import cv2 as cv
import numpy as np
import os

def edge(img):
	#定义结构元素
	kernel = cv.getStructuringElement(cv.MORPH_RECT,(5, 5))
	#闭运算
	closed = cv.morphologyEx(img, cv.MORPH_CLOSE, kernel)
	#开运算
	opened = cv.morphologyEx(img, cv.MORPH_OPEN, kernel)
	#高斯模糊,降低噪声
	blurred = cv.GaussianBlur(opened,(5,5),0)
	#灰度图像
	gray=cv.cvtColor(blurred,cv.COLOR_RGB2GRAY)
	#图像梯度
	xgrad=cv.Sobel(gray,cv.CV_16SC1,1,0)
	ygrad=cv.Sobel(gray,cv.CV_16SC1,0,1)
	#计算边缘
	#50和150参数必须符合1：3或者1：2
	edge_output=cv.Canny(xgrad,ygrad,50,150)
	dst=cv.bitwise_and(gray,gray,mask=edge_output)
	return dst

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

	for i in range(h-640):
		for j in range(w-640):
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
				print(sum_arr)
				return i, j

	return -1, -1

def resize(img):
	h, w = img.shape[:2]
	ratio = 650 / w if h > w else 650 / h
	return cv.resize(img, (0, 0), fx=ratio, fy=ratio, interpolation=cv.INTER_NEAREST)

def process(img_path, img_name):
	img = cv.imread(img_path)
	h, w = img.shape[:2]
	if h < 650 and w < 650:
		return
	resize_img = resize(img)
	cv.imwrite('resize/%s' % img_name, resize_img)
	gray = edge(resize_img)
	cv.imwrite('gray/%s' % img_name, gray)
	si, sj = get_square(gray)
	if si >= 0 and sj >= 0:
		cropped = resize_img[si:si+640, sj:sj+640]
		print('writing %s from (%d, %d)' % (img_name, si, sj))
		cv.imwrite('images/%s' % img_name, cropped)

def process_images(path):
	work_dir = path
	for parent, dirnames, filenames in os.walk(work_dir,  followlinks=True):
		for filename in filenames:
			if not filename.endswith(".jpg"):
				continue
			file_path = os.path.join(parent, filename)
			print('process %s' % filename)
			process(file_path, filename)
			

if __name__ == '__main__':
	path = "raw_images"
	process_images(path)
	'''
	for img_name in ['dog_28.jpg', 'indoor_32.jpg']:
		print(img_name)
		file_path = 'raw_images/%s' % img_name
		img = cv.imread(file_path)
		resize_img = resize(img)
		cv.imwrite('resize/%s' % img_name, resize_img)
		gray = edge(resize_img)
		cv.imwrite('gray/%s' % img_name, gray)
		si, sj = get_square(gray)
		if si >= 0 and sj >= 0:
			cropped = resize_img	[si:si+640, sj:sj+640]
			cv.imwrite('images/%s' % img_name, cropped)
	'''
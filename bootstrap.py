import downloader

def parse_toefl(path):
	with open(path) as f:
		lines = f.readlines()
		for i in range(0, len(lines)):
			args = lines[i].strip().split()
			if len(args) < 3 or not args[2] == "n.":
				continue
			word = args[0]
			try:
				print('start %d %s' % (i, word))
				downloader.run(word)
			except Exception as e:
				print('failed at %d %s' % (i, word))

if __name__ == '__main__':
	parse_toefl('TOEFL.txt')
#!/usr/bin/python

from basesite  import basesite
from threading import Thread
import time

"""
	Downloads flickr albums
"""
class flickr(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'flickr.com' in url:
			raise Exception('')
		if not '/photos/' in url:
			raise Exception('Required /photos/ not found in URL')
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		user = 'unknown'
		if '/photos/' in url:
			users = self.web.between(url, '/photos/', '/')
			if len(users) > 0: user = users[0]
		return 'flickr_%s' % user

	def download(self):
		r = self.web.get(self.url)
		total = '?'
		if '<div class="vsNumbers">' in r:
			count = self.web.between(r, '<div class="vsNumbers">', 'photos')[0].strip()
			while ' '  in count: count = count.replace(' ',  '')
			while '\n' in count: count = count.replace('\n', '')
			if count.isdigit(): total = int(count)
			
		while True:
			# Get images
			links = self.web.between(r, '><a data-track="photo-click" href="', '"')
			for index, link in enumerate(links):
				link = 'http://www.flickr.com%s' % link
				# Download every image
				# Uses superclass threaded download method
				self.download_image(link, index + 1, total=len(links)) 
			if 'data-track="next" href="' in r:
				nextpage = self.web.between(r, 'data-track="next" href="', '"')[0]
				r = self.web.get(nextpage)
			else:
				break
		self.wait_for_threads()
	
	def download_image(self, url, index, total='?', subdir=''):
		while self.thread_count >= self.max_threads:
			time.sleep(0.1)
		self.thread_count += 1
		args = (url, index, total)
		t = Thread(target=self.download_image_thread, args=args)
		t.start()
		
	def download_image_thread(self, url, index, total):
		pid = url[:url.rfind('/in/')]
		pid = pid[pid.rfind('/')+1:]
		larger = url.replace('/in/', '/sizes/o/in/')
		r = self.web.get(url)
		titles = self.web.between(r, 'title="', '"')
		if len(titles) > 0:
			title = self.fix_filename(titles[0])
		else:
			title = 'unknown'
		imgs = self.web.between(r, '<img src="http://farm', '"')
		if len(imgs) == 0:
			self.log('unable to find image @ %s' % url)
		else:
			img = 'http://farm%s' % imgs[0]
			ext = img[img.rfind('.'):]
			saveas = '%s/%03d_%s_%s%s' % (self.working_dir, index, pid, title, ext)
			if self.web.download(img, saveas):
				self.log('downloaded (%d/%s) (%s)' % (index, total, self.get_size(saveas)))
			else:
				self.log('download failed (%d/%s) %s' % (index, total, img))
		self.thread_count -= 1
	
	""" Parses non-filename-safe characters """
	def fix_filename(self, text):
		good = 'abcdefghijklmnopqrstuvwxyz0123456789.'
		result = ''
		for i in xrange(0, len(text)):
			if text[i].lower() in good:
				result += text[i]
			elif text[i] in [' ', '_', '\n']:
				result += '-'
		return result
# -*- coding: utf-8 -*-
import scrapy
from scrapy.exceptions import CloseSpider
from scrapy import Request
# from urlparse import urlparse
from json import loads
from datetime import date
import os, urllib

from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods import posts
# import xmlrpclib
from wordpress_xmlrpc.compat import xmlrpc_client
from wordpress_xmlrpc.methods import media, posts

class flwfishing_scraperSpider(scrapy.Spider):

	name = "flwfishing_scraper"
	wp_url='https://www.fishingwindow.com/xmlrpc.php'
	# wp_url = 'https://www.fishingwindow.com/wp-admin/'
	wp_user = 'suresh'
	wp_pass = '%pxN2V#)9mpFdyHjyghnZA2S'

	start_urls = ['https://www.flwfishing.com/news']

	use_selenium = True
###########################################################

	def __init__(self, *args, **kwargs):
		super(flwfishing_scraperSpider, self).__init__(*args, **kwargs)


###########################################################

	def start_requests(self):
		for url in self.start_urls:
			yield Request(url, callback=self.parse)

###########################################################

	def parse(self, response):
		products = response.xpath('//div[@class="row articleContainer"]')

		# print len(products)
		# print "###########"
		# print response.url

		if not products: return

		for i in products:
			articleTitle = i.xpath('./div/h3/text()').extract_first()
			articleCategories = ['Uncategorized']
			articleContent = i.xpath('./div[@class="col-md-7 columns article-detail-wrapper"]/p/text()').extract()[-1]
			articleTags=[]
			origin_url = i.xpath('./div[@class="col-md-7 columns article-detail-wrapper"]/p/a/@href').extract()[-1].encode('utf8')
			if origin_url:
				origin_url = response.urljoin(origin_url)
			PhotoUrl = i.xpath('./div/div/img/@src').extract_first()
			self.post_article(self.wp_url, self.wp_user, self.wp_pass, articleTitle, articleCategories, articleContent, articleTags, PhotoUrl, origin_url)
			break


	def post_article(self, wpUrl, wpUserName, wpPassword, articleTitle, articleCategories, articleContent, articleTags, PhotoUrl, origin_url):
		self.path=os.getcwd()+"\\00000001.jpg"
		self.articlePhotoUrl=PhotoUrl
		self.wpUrl=wpUrl
		self.wpUserName=wpUserName
		self.wpPassword=wpPassword
		#Download File
		f = open(self.path,'wb')
		f.write(urllib.urlopen(self.articlePhotoUrl).read())
		f.close()
		#Upload to WordPress
		client = Client(self.wpUrl,self.wpUserName,self.wpPassword)
		filename = self.path
		# prepare metadata
		data = {'name': 'picture.jpg','type': 'image/jpg',}

		# read the binary file and let the XMLRPC library encode it into base64
		with open(filename, 'rb') as img:
			data['bits'] = xmlrpc_client.Binary(img.read())
		response = client.call(media.UploadFile(data))
		attachment_id = response['id']
		#Post
		post = WordPressPost()
		post.title = articleTitle
		post.content = '<a href="https://www.flwfishing.com">www.flwfishing.com</a>\n' + articleContent + '<a href="{}">READ MORE</a>'.format(origin_url)
		post.link = origin_url
		post.custom_fields = []
		post.custom_fields.append({
			'key': 'price',
			'value': 2
			})

		post.terms_names = { 'post_tag': articleTags,'category': articleCategories}
		post.post_status = 'publish'
		post.thumbnail = attachment_id
		post.id = client.call(posts.NewPost(post))
		print 'Post Successfully posted. Its Id is: ',post.id

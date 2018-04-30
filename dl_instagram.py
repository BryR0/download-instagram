#!/usr/bin/python
#enconding: utf-8


# /_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
# _/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
# /_/_/_/_/                                      _/_/_/_/_/
# _/_/_/_/  _____  ____  _  ___ ___  _    __    _/_/_/_/_/
# /_/_/_/  / __  \/ __ \/ |/  / __ |/ \  / /   _/_/_/_/_/
# _/_/_/  / /_/ _/ /_/ /\   _/ /_/ /   \/ /   _/_/_/_/_/
# /_/_/  / /__/ / _, _/ /  // _,  / /\   /   _/_/_/_/_/
# _/_/   \_____/_/ |_/ /__//_/ \_/_/  \_/   _/_/_/_/_/
# /_/                                      _/_/_/_/_/
# _/                                      _/_/_/_/_/
# /_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
# _/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
#            +============================+
#            |   [Website By Bryan A.] 	|
#            |     [Bryro.comli.com]	 	|
#            +============================+
#            |   	dl_instagram.py 		|
#            |            v.1.8           |
#            +----------------------------+

import os,json,sys,time,re
import argparse
import requests
import threading


class Instagram(object):
	def __init__(self,profile,login_user,login_password,media=3):
		#self.url = "https://www.instagram.com/%s/?__a=1"
		self.url = "https://www.instagram.com/%s/"
		self.query_url = 'https://www.instagram.com/graphql/query/?query_hash=472f257a40c653c64c666ce877d59d2b' \
			'&variables=%7B%22id%22%3A%22{user_id}%22%2C%22first%22%3A{count}%2C%22after%22%3A%22{after}%22%7D'
		self.profile = profile
		self.user_id = login_user
		self.password = login_password
		self.folder=""
		self.profile_id=""
		self.login_status=False
		self.images=True
		self.videos =True
		self.thread =True
		self.has_next_page=True
		self.s=requests.Session()
		self.header = {
			"User-Agent":"Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0"
		}

		media=int(media)

		if media == 1 :
			self.videos = False
		elif media == 2 :
			self.images = False

	def insta(self):
		self.folder=self.profile
		if self.user_id !='' and self.password !='':
			login=self.login()
			if login==False:
				print("Invalid username or password")
				sys.exit(1)

		if self.profile.find('#') ==0:
			self.profile=self.profile.replace("#", "")
			self.url='https://www.instagram.com/explore/tags/%s/?__a=1'
			jsondata = self.check_hashtag()
			if not jsondata ==False:
				self.download_hash(jsondata)

		else:
			jsondata= self.checkusername()
			if not jsondata==False:
				self.download(jsondata)

	def rquery(self,url,json=True,stream=False):
		try:
			reconnect=True;
			count=0
			while reconnect:
				if self.login_status and stream==False:
					r=self.s.get(url)
				else:
					r=requests.get(url,headers=self.header,stream=stream)

				if(r.status_code==200):
					reconnect=False
					count=0

					if json:
						return r.json()
					else:
						return r;
				else:
					print "[-] conexion broken waiting 5 seconds for next trying"
					if count <= 10:
						count=count+1
						time.sleep(5)
					else:
						print "[+] conexion exede continue with next!"
						reconnect=False
			return reconnect

		except Exception as e:
			pass

	def checkusername(self):

		url_profile=self.url % self.profile
		folder=self.folder
		next_stage=False

		if not self.login_status:
			print("ups need login")
			exit(1)


		check = self.rquery(url_profile,False).text

		json_data=json.loads(check.split("window._sharedData = ")[1].split(";</script>")[0])['entry_data']['ProfilePage'][0]

		if json_data["graphql"]['user']['edge_owner_to_timeline_media']['count']==0 :
			print("No posts")
			return False
		else:

			if json_data["graphql"]['user']['followed_by_viewer'] == False:
				print("You don't have previliges to access "+self.profile+" profile")
				sys.exit(1)
			else:
				self.creating_folder(folder)
				next_stage=True

		if next_stage:
			self.profile_id= str(json_data['graphql']['user']['edge_owner_to_timeline_media']['edges'][0]['node']['owner']['id'])

			return json_data

		return next_stage


	def check_hashtag(self):

		tag= self.url % self.profile
		publicjson=self.rquery(tag)
		folder=self.folder

		if publicjson: 
			if publicjson["graphql"]["hashtag"]["edge_hashtag_to_media"]["count"] == 0:
				print("No posts")
				return False
			else:
				if self.login_status==False:
					print("trying to download public profile..")
					self.creating_folder(folder)
					return publicjson
				else:
					privatejson = self.rquery(tag)
					self.creating_folder(folder)
					return  privatejson
		else:
			return False


	def creating_folder(self,folder):

		if not os.path.exists(folder):
			print("Creating "+folder+" folder...")
			os.makedirs(folder)
			self.folder =folder+"/"
			return True
		else:
			for i in range(1,100):			
				newfolder = folder+"("+str(i+1)+")"
				if not os.path.exists(newfolder):
					f=self.creating_folder(newfolder)
					return f
					break
		
	def download(self,jsondata,page=False):

		if page:
			index_1='data'
		else:
			index_1='graphql'

		collectingNodes = list(jsondata[index_1]['user']['edge_owner_to_timeline_media']['edges'])
		
		try:
			if not len(collectingNodes) == 0:
				for k in collectingNodes:
					if k['node']['__typename'] == 'GraphImage' and self.images :
						imageurl = k['node']['display_url']
						filename = k['node']['id']
						self.thread = threading.Thread(target=self.download_file, args=(imageurl,filename,))
						self.thread.start()

					elif k['node']['__typename'] == 'GraphSidecar' :
						self.thread = threading.Thread(target=self.download_array, args=(k['node']['shortcode'],))
						self.thread.start()


					elif k['node']['__typename'] == 'GraphVideo' and self.videos:
						self.thread = threading.Thread(target=self.download_video, args=(k['node']['shortcode'],))
						self.thread.start()

		except Exception:
			pass

		has_next = jsondata[index_1]['user']['edge_owner_to_timeline_media']['page_info']
		self.has_next_page = has_next['has_next_page']

		if self.has_next_page :
			restart_cursor = has_next['end_cursor']

			url_rewriting=self.query_url.format(user_id=self.profile_id, count=50,after=restart_cursor)
			parsed_json = self.rquery(url_rewriting)
			self.download(parsed_json,True)


	def download_hash(self,jsondata):
		url_p='https://www.instagram.com/p/%s/?__a=1'
		if jsondata['graphql']['hashtag']['edge_hashtag_to_media']['edges']:
			media_tag=list(jsondata['graphql']['hashtag']['edge_hashtag_to_media']['edges'])
			post_tag=list(jsondata['graphql']['hashtag']['edge_hashtag_to_top_posts']['edges'])
			total=jsondata['graphql']['hashtag']['edge_hashtag_to_media']['count']
			restart_cursor=jsondata['graphql']['hashtag']['edge_hashtag_to_media']['page_info']['end_cursor']
			self.has_next_page=jsondata['graphql']['hashtag']['edge_hashtag_to_media']['page_info']['has_next_page']


			for d in media_tag:
				self.thread = threading.Thread(target=self.type_file, args=(d['node']['shortcode'],))
				self.thread.start()


			for p in post_tag:
				self.thread = threading.Thread(target=self.type_file, args=(d['node']['shortcode'],))
				self.thread.start()


			if self.has_next_page :
				nurl=self.url % self.profile
				url_rewriting = nurl+'&max_id='+str(restart_cursor)
				parsed_json = self.rquery(url_rewriting)
				self.download_hash(parsed_json)
		return False

	def type_file(self,code):
		url_p="https://www.instagram.com/p/%s/?__a=1"
		url2 =url_p % code
		data=""
		file_url=""
		
		data = self.rquery(str(url2))

		try:
			if data:
				file_type=data['graphql']['shortcode_media']['__typename']
				file_url=data['graphql']['shortcode_media']
				file_name=data['graphql']['shortcode_media']['id']

				if file_type=='GraphVideo' and self.videos:
					url_file=file_url['video_url']

				if file_type=='GraphImage' and self.images:
					url_file=file_url['display_url']

		        query=self.download_file(url_file,file_name)
		        if not query:
		        	return False
			else:
				return False
		except Exception as e:
			pass

	def download_video(self,code):
		url_p='https://www.instagram.com/p/%s/?__a=1'
		url2 = url_p % code

		data2 = self.rquery(url2)

		videourl = data2['graphql']['shortcode_media']
		self.download_file(videourl['video_url'],videourl['id'])

	def download_file(self,file_url,filename):

		r = self.rquery(file_url,False,True)
		# int(r.headers.get('content-length', 0))

		count=0
		file_ext= file_url[-4:]

		print("\rDownloading "+filename+file_ext)
		with open(self.folder+filename+file_ext,"wb") as f:
			for chunk in r.iter_content(chunk_size=1024):
				if chunk:
					f.write(chunk)
					f.flush()
            		os.fsync(f.fileno())
            	if not chunk:
            		if count <=10:
                		print "[-] conexion broken re-download started in 5 seconds"
                		sys.sleep(5)
                		count=count+1
                		self.download_file(file_url,filename)
                	else:
                		return False
			f.close()

	def download_array(self,code):
		url1 = 'https://www.instagram.com/p/%s/?__a=1'

		data1=self.rquery(str(url1 % code))

		fileurl = data1['graphql']['shortcode_media']['edge_sidecar_to_children']['edges']
	
		try:
			k = 1
			i = 0
			while k :
				if fileurl[i]['node']['__typename'] == "GraphVideo" and self.videos:
					self.download_file(fileurl[i]['node']['video_url'],fileurl[i]['node']['id'])
				elif fileurl[i]['node']['__typename'] == "GraphImage" and self.images:
					self.download_file(fileurl[i]['node']['display_url'],fileurl[i]['node']['id'])
				i = i+1
				k = k+1
		except IndexError:
			pass

	def login(self):
		print 'Trying to login as %s...\n' % (self.user_id)
		self.s.headers.update({
			'Accept': '*/*',
			'Accept-Encoding' : 'gzip, deflate',
			'Accept-Language' : 'en-US;q=0.6,en;q=0.4',
			'authority': 'www.instagram.com',
			'ContentType' : 'application/x-www-form-urlencoded',
			'Connection': 'keep-alive',
			'Host' : 'www.instagram.com',
			'origin': 'https://www.instagram.com',
			'Referer': 'https://www.instagram.com',
			'Upgrade-Insecure-Requests':'1',
			'UserAgent':'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0',
			'x-instagram-ajax':'1',
			'X-Requested-With': 'XMLHttpRequest'
		})
		r = self.s.get('https://www.instagram.com/') 
		self.s.headers.update({'X-CSRFToken' : r.cookies.get_dict()['csrftoken']})
		r = self.s.post('https://www.instagram.com/accounts/login/ajax/', data={'username':self.user_id, 'password':self.password}, allow_redirects=True)
		self.s.headers.update({'X-CSRFToken' : r.cookies.get_dict()['csrftoken']})
		loginstatus = json.loads(r.text)
		if loginstatus['authenticated'] == True :
			print 'Login Success'
			self.login_status=True
			return True
		elif loginstatus['authenticated'] == False :
			return False
	def __del__(self):
		if not self.has_next_page:
			print('\n\n************Download Completed************')


if __name__ == '__main__':
	
	parser = argparse.ArgumentParser()
	parser.add_argument('-u', action="store", dest="login_user",default="",help='username propio')
	parser.add_argument('-p', action="store", dest="login_password",help='Password')
	parser.add_argument('-n', action="store", dest="profilename",help='nombre del perfil a descargar')
	parser.add_argument('-t', action="store", dest="type",default=3,help='file type: 1=image,2=video,3(default)=all')
	results = parser.parse_args()

	if len(sys.argv)==1 or results.profilename=='':
	    parser.print_help()
	    sys.exit(1)

	
	if len(sys.argv)>1:	
		start=Instagram(results.profilename,results.login_user,results.login_password,results.type)
		start.insta()

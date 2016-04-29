LOGIN_URL = 'https://www.itjuzi.com/user/login'
FORM_INFO = {
	'create_account_email' : 'zhangshuosc@163.com',
	'create_account_password' : '08251218'
}
BASE_URLS = [
{'url': 'https://www.itjuzi.com/investevents?scope=47&page=', 'type': 'demostic_ivst'},
{'url': 'http://www.itjuzi.com/company?scope=47&page=', 'type': 'demostic_comp'}
]
FILTER_SIZE = 1000000
FILTER_ERROR_RATE = 0.001

MAX_DUP_URL = 2

MYSQL = {
	'host': 'localhost',
	'username': 'xiao',
	'password': 'xiao',
	'database': 'vcbeat'
}

MONGODB = {
	'host': 'localhost',
	'port': 27017,
	'database': 'vcbeat',
	'raw_collection': 'html_snapshot',
	'img_collection': 'img_snapshot'
}

NOTIFY_MAIL = {
	'HOST': 'smtp.163.com',
	'FROM': {
		'MAIL': 'vcbeat_spider_team@163.com',
		'PASSWORD': 'vcbeat001'
	},
	'TO_LIST':['xiaolihaoict@gmail.com']
}



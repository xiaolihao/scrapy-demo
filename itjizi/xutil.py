import spiders.user_settings
import pymongo
import smtplib
from email.mime.text import MIMEText

class Util:
    db = None
    conn = None

    @staticmethod
    def get_mongodb():
        if Util.db is None:
             connection = pymongo.MongoClient(
                    spiders.user_settings.MONGODB['host'],
                    spiders.user_settings.MONGODB['port']
            )
             Util.db = connection[spiders.user_settings.MONGODB['database']]
        return Util.db

    @staticmethod
    def is_connected():
        try:
            status = Util.conn.noop()[0]
        except:
            status = -1
        return True if status == 250 else False


    @staticmethod
    def send_mail(host, _from, _password, to_list, content):
        msg = MIMEText(content,_subtype='plain')
        msg['Subject'] = 'spider-debug-info'
        msg['From'] = _from
        msg['To'] = ';'.join(to_lists)
        try:
            if not Util.is_connected():
                Util.conn = smtplib.SMTP()
                Util.conn.connect(host)
                Util.conn.login(_from, _password)

            Util.conn.sendmail(_from, to_list, msg.as_string())
        except Exception, e:
            print str(e)





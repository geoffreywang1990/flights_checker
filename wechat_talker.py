import requests
import json
from wechat_credential import AppID, AppSecret


class WechatTalker:
    url_token = 'https://api.weixin.qq.com/cgi-bin/token?'
    url_msg ='https://api.weixin.qq.com/cgi-bin/message/custom/send?'
    url_user_info = 'https://api.weixin.qq.com/cgi-bin/user/info?'
    url_user_list = 'https://api.weixin.qq.com/cgi-bin/user/get?'

    def __init__(self):
        self.update_token();

    def update_token(self):
        res = requests.get(url=self.url_token,params={
                 "grant_type": 'client_credential',
                 'appid':AppID,# 这里填写上面获取到的appID
                 'secret':AppSecret,# 这里填写上面获取到的appsecret
                 }).json()
        self.Token = res.get('access_token')
        print(res)

    def get_token(self):
        if self.Token is None:
            self.update_token()
        return self.Token


    def send_text_msg(self, user_id, content):
        body = {
                "touser": user_id,
                "msgtype":"text",
                "text":{
                 "content":content
                }
            }
         
        res =requests.post(url=self.url_msg,params = {
                 'access_token': self.get_token()
            },data=json.dumps(body,ensure_ascii=False).encode('utf-8'))

    def get_user_list(self):
        res =requests.post(url=self.url_user_list,params = {
                 'access_token': self.get_token() 
                 }).json()
        self.user_id_list = res['data']['openid'] 
        self.print_all_users()
        
    def get_user_info(self,user_id):
        res =requests.post(url=self.url_user_info,params = {
                 'access_token': self.get_token(),
                 'openid': user_id,
                 }).json()
        return res

    def print_all_users(self):
        for user_id in self.user_id_list:
            print("{} : {}".format(self.get_user_info(user_id)['nickname'], user_id))


if __name__ == '__main__':
    a = WechatTalker() 
    a.get_user_list()

    

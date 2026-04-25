import requests
from app.config.config import Config

MOCK_OPENIDS = {
    'test_code_1': 'oTestOpenid123456',
    'test_code_2': 'oTestOpenid789012',
    'test_code_3': 'oTestOpenid345678',
}

class WeChatService:
    
    @staticmethod
    def code2session(code):
        if Config.DEBUG:
            if code in MOCK_OPENIDS:
                return {
                    'openid': MOCK_OPENIDS[code],
                    'session_key': 'mock_session_key_' + code,
                    'errcode': 0
                }
            else:
                return {
                    'openid': 'oMockOpenid' + code[-6:],
                    'session_key': 'mock_session_key_' + code,
                    'errcode': 0
                }
        
        url = 'https://api.weixin.qq.com/sns/jscode2session'
        params = {
            'appid': Config.WECHAT_APPID,
            'secret': Config.WECHAT_SECRET,
            'js_code': code,
            'grant_type': 'authorization_code'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            if 'errcode' in result and result['errcode'] != 0:
                return {
                    'errcode': result.get('errcode'),
                    'errmsg': result.get('errmsg', '微信登录失败')
                }
            
            return result
        except requests.exceptions.RequestException as e:
            return {
                'errcode': -1,
                'errmsg': f'请求微信API失败: {str(e)}'
            }

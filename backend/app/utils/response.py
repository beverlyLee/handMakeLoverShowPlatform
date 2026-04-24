from app.common.response_code import ResponseCode, ResponseCodeMsg

def success(data=None, msg=ResponseCodeMsg.SUCCESS.value):
    return {
        'code': ResponseCode.SUCCESS.value,
        'msg': msg,
        'data': data
    }

def error(code=ResponseCode.ERROR, msg=None, data=None):
    if isinstance(code, ResponseCode):
        code_value = code.value
        if msg is None:
            try:
                msg_enum = ResponseCodeMsg[code.name]
                msg = msg_enum.value
            except KeyError:
                msg = ResponseCodeMsg.ERROR.value
    else:
        code_value = code
        if msg is None:
            msg = ResponseCodeMsg.ERROR.value
    
    return {
        'code': code_value,
        'msg': msg,
        'data': data
    }

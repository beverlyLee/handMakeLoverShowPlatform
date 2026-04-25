from enum import Enum

class ResponseCode(Enum):
    SUCCESS = 0
    ERROR = 1
    
    PARAM_ERROR = 1001
    PARAM_MISSING = 1002
    PARAM_INVALID = 1003
    
    AUTH_FAILED = 2001
    TOKEN_MISSING = 2002
    TOKEN_INVALID = 2003
    TOKEN_EXPIRED = 2004
    
    USER_NOT_FOUND = 3001
    USER_EXISTS = 3002
    USER_PASSWORD_ERROR = 3003
    
    DATA_NOT_FOUND = 4001
    DATA_EXISTS = 4002
    DATA_DELETE_FAILED = 4003
    DATA_UPDATE_FAILED = 4004
    DATA_CREATE_FAILED = 4005
    
    PERMISSION_DENIED = 5001
    ROLE_NOT_ALLOWED = 5002
    
    SYSTEM_ERROR = 9999

class ResponseCodeMsg(Enum):
    SUCCESS = "操作成功"
    ERROR = "操作失败"
    
    PARAM_ERROR = "参数错误"
    PARAM_MISSING = "参数缺失"
    PARAM_INVALID = "参数无效"
    
    AUTH_FAILED = "认证失败"
    TOKEN_MISSING = "Token缺失"
    TOKEN_INVALID = "Token无效"
    TOKEN_EXPIRED = "Token已过期"
    
    USER_NOT_FOUND = "用户不存在"
    USER_EXISTS = "用户已存在"
    USER_PASSWORD_ERROR = "密码错误"
    
    DATA_NOT_FOUND = "数据不存在"
    DATA_EXISTS = "数据已存在"
    DATA_DELETE_FAILED = "数据删除失败"
    DATA_UPDATE_FAILED = "数据更新失败"
    DATA_CREATE_FAILED = "数据创建失败"
    
    PERMISSION_DENIED = "权限不足"
    ROLE_NOT_ALLOWED = "角色不允许"
    
    SYSTEM_ERROR = "系统错误"

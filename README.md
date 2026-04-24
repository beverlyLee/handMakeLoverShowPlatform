# 手工爱好者展示平台

## 项目简介

这是一个面向手工爱好者的综合性展示与交易平台，采用**前后端分离架构**，前端为微信小程序，后端为Python Flask服务。平台旨在连接手工创作者与爱好者，提供作品展示、在线交易、订单管理等一体化服务。

### 项目背景

随着手工DIY文化的兴起，越来越多的手工创作者需要一个专业的平台来展示和销售自己的作品，同时手工爱好者也希望能够方便地浏览、购买心仪的手工作品。本平台应运而生，致力于打造一个专业、友好的手工爱好者社区。

### 目标用户

- **客户**：手工爱好者、手工作品消费者，浏览作品、在线下单
- **老师/创作者**：手工创作者、手作达人，展示作品、接收订单、管理作品

## 技术栈

### 前端技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| 微信小程序 | - | 原生开发框架 |
| 微信开发者工具 | 最新版 | 开发调试工具 |
| WXML/WXSS | - | 小程序标记语言和样式语言 |
| JavaScript | ES6+ | 小程序逻辑开发 |

### 后端技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| Python | 3.8+ | 开发语言 |
| Flask | 2.0+ | Web框架 |
| SQLite | - | 开发环境数据库 |
| MySQL | 5.7+ | 生产环境数据库 |
| Flask-RESTful | - | RESTful API扩展 |
| Flask-JWT-Extended | - | JWT身份认证 |
| Flask-SQLAlchemy | - | ORM框架 |
| Flask-CORS | - | 跨域支持 |

### 开发工具

- **代码编辑器**：VS Code / PyCharm
- **API测试**：Postman / 微信开发者工具
- **版本控制**：Git
- **虚拟环境**：venv

## 核心功能

### 客户功能模块

#### 1. 作品浏览与搜索
- 首页作品列表展示（按分类、热门、最新排序）
- 作品分类筛选（手工饰品、手工皮具、陶艺、编织等）
- 关键词搜索功能
- 作品轮播图推荐
- 作品详情查看（价格、材料、制作周期、创作者信息）

#### 2. 个人中心
- 微信授权登录
- 个人信息查看与编辑
- 我的收藏夹
- 我的订单（全部、待付款、待发货、待收货、已完成）
- 收货地址管理
- 系统消息通知

#### 3. 订单管理
- 创建订单（选择作品、确认地址、选择数量）
- 订单状态跟踪
- 订单详情查看
- 订单评价功能
- 订单取消（未付款状态）

#### 4. 地址管理
- 收货地址列表
- 新增收货地址
- 编辑收货地址
- 删除收货地址
- 设置默认地址

### 老师/创作者功能模块

#### 1. 作品管理
- 作品发布（上传图片、填写详情、设置价格、分类）
- 作品列表管理（上下架、编辑、删除）
- 作品库存管理
- 作品销量统计

#### 2. 订单管理
- 订单列表查看（按状态筛选）
- 订单详情查看
- 订单状态更新（确认订单、发货、完成订单）
- 订单消息通知

#### 3. 角色切换
- 客户/老师身份切换
- 角色权限控制

#### 4. 老师主页
- 个人店铺展示
- 作品列表展示
- 店铺信息编辑
- 粉丝/关注管理

### 通用功能模块

#### 1. 用户认证
- 微信小程序授权登录
- 手机号绑定
- 登录状态维护
- 权限控制

#### 2. 收藏功能
- 作品收藏/取消收藏
- 收藏列表查看

#### 3. 消息通知
- 系统消息
- 订单状态变更通知
- 新订单提醒

#### 4. 搜索功能
- 作品关键词搜索
- 搜索历史记录
- 热门搜索推荐

## 目录结构

```
handMakeLoverShowPlatform/
├── backend/                          # Python Flask后端
│   ├── app/                          # Flask应用主目录
│   │   ├── __init__.py              # 应用初始化
│   │   ├── config/                   # 配置文件目录
│   │   │   ├── __init__.py
│   │   │   └── config.py            # 配置文件（数据库、JWT等）
│   │   ├── routes/                   # 路由模块
│   │   │   ├── __init__.py          # 路由注册
│   │   │   ├── auth.py              # 认证相关接口（登录、注册）
│   │   │   ├── users.py             # 用户信息接口
│   │   │   ├── products.py          # 作品相关接口
│   │   │   ├── orders.py            # 订单相关接口
│   │   │   ├── cart.py              # 购物车接口
│   │   │   ├── favorites.py         # 收藏夹接口
│   │   │   ├── reviews.py           # 评价相关接口
│   │   │   ├── search.py            # 搜索接口
│   │   │   ├── messages.py          # 消息通知接口
│   │   │   └── main.py              # 主页面接口
│   │   ├── models/                   # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py              # 用户模型
│   │   │   ├── product.py           # 作品模型
│   │   │   ├── order.py             # 订单模型
│   │   │   ├── cart.py              # 购物车模型
│   │   │   ├── favorite.py          # 收藏模型
│   │   │   ├── review.py            # 评价模型
│   │   │   ├── address.py           # 地址模型
│   │   │   └── message.py           # 消息模型
│   │   ├── utils/                    # 工具函数
│   │   │   ├── __init__.py
│   │   │   ├── response.py          # 统一响应格式
│   │   │   ├── decorators.py        # 装饰器（登录验证等）
│   │   │   ├── upload.py            # 文件上传工具
│   │   │   └── wechat.py            # 微信相关工具
│   │   └── extensions.py            # Flask扩展初始化
│   ├── common-utils/                 # 公共工具模块
│   ├── mock-data/                    # 模拟数据
│   ├── data/                         # 数据存储
│   ├── venv/                         # Python虚拟环境
│   ├── requirements.txt              # Python依赖包
│   └── run.py                        # 应用启动文件
│
├── handicraft-miniprogram/          # 微信小程序前端（可选项目）
│   ├── miniprogram/                  # 小程序主目录
│   │   ├── address-manage/          # 地址管理页面
│   │   ├── home-work-show/          # 首页作品展示
│   │   ├── work-detail/             # 作品详情页面
│   │   ├── user-center/             # 用户中心
│   │   ├── role-switch/             # 角色切换页面
│   │   ├── order-create/            # 订单创建页面
│   │   ├── order-list/              # 订单列表页面
│   │   ├── order-operate/           # 订单操作页面
│   │   ├── teacher-home/            # 老师主页
│   │   └── common-utils/            # 公共工具
│   └── backend/                      # 对应后端（可选）
│
├── .gitignore                        # Git忽略文件
└── README.md                         # 项目说明文档
```

## 后端API接口说明

### 统一响应格式

所有API接口返回统一的JSON格式：

```json
{
    "code": 0,
    "msg": "success",
    "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 状态码，0表示成功，非0表示失败 |
| msg | string | 消息描述 |
| data | object/array | 返回数据 |

### 认证模块 (auth.py)

| 接口 | 方法 | 描述 | 需要登录 |
|------|------|------|----------|
| `/api/auth/login` | POST | 微信登录 | 否 |
| `/api/auth/register` | POST | 用户注册 | 否 |
| `/api/auth/refresh` | POST | 刷新Token | 否 |
| `/api/auth/profile` | GET | 获取当前用户信息 | 是 |

#### 登录接口示例

**请求**：
```
POST /api/auth/login
Content-Type: application/json

{
    "code": "wx_login_code",
    "nickname": "用户昵称",
    "avatar": "头像URL"
}
```

**响应**：
```json
{
    "code": 0,
    "msg": "登录成功",
    "data": {
        "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "user_info": {
            "id": 1,
            "nickname": "用户昵称",
            "avatar": "头像URL",
            "role": "customer",
            "phone": "13800138000"
        }
    }
}
```

### 用户模块 (users.py)

| 接口 | 方法 | 描述 | 需要登录 |
|------|------|------|----------|
| `/api/users/profile` | GET | 获取用户信息 | 是 |
| `/api/users/profile` | PUT | 更新用户信息 | 是 |
| `/api/users/role` | PUT | 切换角色 | 是 |
| `/api/users/address` | GET | 获取地址列表 | 是 |
| `/api/users/address` | POST | 新增地址 | 是 |
| `/api/users/address/<id>` | PUT | 更新地址 | 是 |
| `/api/users/address/<id>` | DELETE | 删除地址 | 是 |
| `/api/users/address/<id>/default` | PUT | 设为默认地址 | 是 |

### 作品模块 (products.py)

| 接口 | 方法 | 描述 | 需要登录 |
|------|------|------|----------|
| `/api/products` | GET | 获取作品列表 | 否 |
| `/api/products/<id>` | GET | 获取作品详情 | 否 |
| `/api/products` | POST | 发布作品 | 是（老师） |
| `/api/products/<id>` | PUT | 更新作品 | 是（老师） |
| `/api/products/<id>` | DELETE | 删除作品 | 是（老师） |
| `/api/products/categories` | GET | 获取作品分类 | 否 |
| `/api/products/my` | GET | 获取我的作品 | 是（老师） |

#### 获取作品列表接口示例

**请求**：
```
GET /api/products?page=1&size=10&category=1&sort=new
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| size | int | 否 | 每页数量，默认10 |
| category | int | 否 | 分类ID |
| sort | string | 否 | 排序方式：new(最新), hot(热门), price_asc(价格升序), price_desc(价格降序) |
| keyword | string | 否 | 搜索关键词 |

**响应**：
```json
{
    "code": 0,
    "msg": "success",
    "data": {
        "list": [
            {
                "id": 1,
                "title": "手工编织羊毛围巾",
                "price": 199.00,
                "original_price": 299.00,
                "cover": "https://example.com/image.jpg",
                "category": "编织",
                "category_id": 1,
                "sales": 128,
                "is_favorite": false,
                "teacher": {
                    "id": 1,
                    "nickname": "手工达人",
                    "avatar": "https://example.com/avatar.jpg"
                },
                "created_at": "2024-01-15 10:30:00"
            }
        ],
        "total": 100,
        "page": 1,
        "size": 10,
        "total_pages": 10
    }
}
```

### 订单模块 (orders.py)

| 接口 | 方法 | 描述 | 需要登录 |
|------|------|------|----------|
| `/api/orders` | GET | 获取订单列表 | 是 |
| `/api/orders/<id>` | GET | 获取订单详情 | 是 |
| `/api/orders` | POST | 创建订单 | 是 |
| `/api/orders/<id>/cancel` | POST | 取消订单 | 是 |
| `/api/orders/<id>/pay` | POST | 支付订单 | 是 |
| `/api/orders/<id>/confirm` | POST | 确认收货 | 是 |
| `/api/orders/<id>/review` | POST | 评价订单 | 是 |
| `/api/orders/<id>/status` | PUT | 更新订单状态 | 是（老师） |
| `/api/orders/teacher` | GET | 获取老师订单列表 | 是（老师） |

#### 创建订单接口示例

**请求**：
```
POST /api/orders
Content-Type: application/json
Authorization: Bearer <token>

{
    "product_id": 1,
    "quantity": 2,
    "address_id": 1,
    "remark": "请用粉色包装"
}
```

**响应**：
```json
{
    "code": 0,
    "msg": "订单创建成功",
    "data": {
        "order_id": "ORD202401150001",
        "total_amount": 398.00,
        "status": "pending_payment"
    }
}
```

### 订单状态说明

| 状态码 | 状态值 | 说明 |
|--------|--------|------|
| pending_payment | 待付款 | 订单创建后，等待用户付款 |
| pending_confirm | 待确认 | 已付款，等待老师确认订单 |
| pending_shipment | 待发货 | 老师已确认，等待发货 |
| shipped | 已发货 | 已发货，等待收货 |
| completed | 已完成 | 已确认收货 |
| cancelled | 已取消 | 订单已取消 |

### 收藏模块 (favorites.py)

| 接口 | 方法 | 描述 | 需要登录 |
|------|------|------|----------|
| `/api/favorites` | GET | 获取收藏列表 | 是 |
| `/api/favorites` | POST | 添加收藏 | 是 |
| `/api/favorites/<product_id>` | DELETE | 取消收藏 | 是 |

### 搜索模块 (search.py)

| 接口 | 方法 | 描述 | 需要登录 |
|------|------|------|----------|
| `/api/search` | GET | 搜索作品 | 否 |
| `/api/search/history` | GET | 获取搜索历史 | 是 |
| `/api/search/hot` | GET | 获取热门搜索 | 否 |

### 消息模块 (messages.py)

| 接口 | 方法 | 描述 | 需要登录 |
|------|------|------|----------|
| `/api/messages` | GET | 获取消息列表 | 是 |
| `/api/messages/<id>` | GET | 获取消息详情 | 是 |
| `/api/messages/<id>/read` | PUT | 标记已读 | 是 |
| `/api/messages/unread` | GET | 获取未读数量 | 是 |

## 数据库设计

### 用户表 (users)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| openid | String(64) | 微信openid |
| unionid | String(64) | 微信unionid |
| nickname | String(64) | 昵称 |
| avatar | String(255) | 头像URL |
| phone | String(20) | 手机号 |
| role | String(20) | 角色：customer/teacher |
| is_teacher | Boolean | 是否为老师 |
| teacher_verified | Boolean | 老师认证状态 |
| introduction | Text | 个人简介 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 作品表 (products)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| teacher_id | Integer | 创作者ID |
| category_id | Integer | 分类ID |
| title | String(128) | 作品标题 |
| description | Text | 作品描述 |
| price | Decimal(10,2) | 价格 |
| original_price | Decimal(10,2) | 原价 |
| stock | Integer | 库存 |
| sales | Integer | 销量 |
| cover | String(255) | 封面图 |
| images | Text | 详情图（JSON数组） |
| material | String(128) | 材料 |
| craft | String(128) | 工艺 |
| production_cycle | String(64) | 制作周期 |
| is_on_sale | Boolean | 是否上架 |
| is_hot | Boolean | 是否热门 |
| view_count | Integer | 浏览量 |
| favorite_count | Integer | 收藏量 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 订单表 (orders)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| order_no | String(32) | 订单号 |
| customer_id | Integer | 客户ID |
| teacher_id | Integer | 老师ID |
| product_id | Integer | 作品ID |
| product_title | String(128) | 作品标题快照 |
| product_price | Decimal(10,2) | 作品价格快照 |
| product_image | String(255) | 作品图片快照 |
| quantity | Integer | 数量 |
| total_amount | Decimal(10,2) | 订单总金额 |
| status | String(32) | 订单状态 |
| address_name | String(64) | 收货人姓名 |
| address_phone | String(20) | 收货人电话 |
| address_detail | String(255) | 收货地址详情 |
| remark | String(512) | 备注 |
| cancel_reason | String(255) | 取消原因 |
| payment_time | DateTime | 付款时间 |
| confirm_time | DateTime | 确认时间 |
| ship_time | DateTime | 发货时间 |
| complete_time | DateTime | 完成时间 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 其他表

- **categories**：作品分类表
- **addresses**：收货地址表
- **favorites**：收藏表
- **reviews**：评价表
- **messages**：消息表
- **cart**：购物车表（可选）

## 快速开始

### 环境准备

确保你的开发环境已安装：

- Python 3.8 或更高版本
- pip（Python包管理器）
- 微信开发者工具
- Git

### 后端安装与运行

#### 1. 克隆项目

```bash
git clone <repository-url>
cd handMakeLoverShowPlatform
```

#### 2. 创建虚拟环境

```bash
cd backend
python3 -m venv venv
```

#### 3. 激活虚拟环境

**macOS/Linux**：
```bash
source venv/bin/activate
```

**Windows**：
```bash
venv\Scripts\activate
```

#### 4. 安装依赖

```bash
pip install -r requirements.txt
```

#### 5. 配置环境变量

创建 `.env` 文件或修改 `config.py`：

```python
# config.py 示例配置
class Config:
    SECRET_KEY = 'your-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///handicraft.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT配置
    JWT_SECRET_KEY = 'your-jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24小时
    
    # 微信小程序配置
    WECHAT_APP_ID = 'your-app-id'
    WECHAT_APP_SECRET = 'your-app-secret'
    
    # 上传配置
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
```

#### 6. 初始化数据库

```bash
# 进入Python shell
python

# 在Python shell中执行
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
```

#### 7. 运行开发服务器

```bash
python run.py
```

服务器将在 `http://127.0.0.1:5000` 启动

### 前端安装与运行

#### 1. 打开微信开发者工具

#### 2. 导入项目

- 选择「导入项目」
- 项目目录选择 `handicraft-miniprogram/miniprogram` 或你的小程序目录
- 填入你的小程序 AppID（或使用测试号）

#### 3. 配置API地址

修改小程序的配置文件，将API地址指向你的后端服务：

```javascript
// 示例：utils/config.js
const config = {
    baseUrl: 'http://127.0.0.1:5000/api',  // 开发环境
    // baseUrl: 'https://api.yourdomain.com/api',  // 生产环境
    timeout: 10000
};

export default config;
```

#### 4. 编译运行

点击微信开发者工具的「编译」按钮即可预览项目

## 开发规范

### 后端开发规范

#### 代码风格

- 遵循 PEP 8 规范
- 使用 4 空格缩进
- 变量命名使用 snake_case
- 类命名使用 PascalCase
- 常量命名使用 UPPER_SNAKE_CASE

#### API设计规范

- RESTful 风格
- 统一使用 `/api` 前缀
- 接口版本控制（如 `/api/v1/`）
- 使用正确的 HTTP 方法：
  - GET：获取资源
  - POST：创建资源
  - PUT：更新资源
  - DELETE：删除资源

#### 响应格式规范

```python
# 成功响应
{
    "code": 0,
    "msg": "success",
    "data": {...}
}

# 失败响应
{
    "code": 1001,
    "msg": "参数错误",
    "data": null
}
```

#### 错误码定义

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1001 | 参数错误 |
| 1002 | 缺少必要参数 |
| 2001 | 未登录 |
| 2002 | Token无效 |
| 2003 | Token已过期 |
| 2004 | 权限不足 |
| 3001 | 用户不存在 |
| 3002 | 密码错误 |
| 3003 | 用户已存在 |
| 4001 | 作品不存在 |
| 4002 | 作品已下架 |
| 4003 | 库存不足 |
| 5001 | 订单不存在 |
| 5002 | 订单状态错误 |
| 5003 | 订单已取消 |
| 9001 | 服务器内部错误 |
| 9002 | 数据库操作失败 |

### 前端开发规范

#### 页面结构

每个页面应包含以下文件：

```
page-name/
├── page-name.js      # 页面逻辑
├── page-name.json    # 页面配置
├── page-name.wxml    # 页面结构
└── page-name.wxss    # 页面样式
```

#### 命名规范

- 页面文件名使用 kebab-case
- JavaScript 变量使用 camelCase
- 组件命名使用 kebab-case
- CSS 类名使用 kebab-case

#### API封装

统一封装请求方法：

```javascript
// utils/request.js
const config = require('./config');

function request(options) {
    return new Promise((resolve, reject) => {
        wx.request({
            url: config.baseUrl + options.url,
            method: options.method || 'GET',
            data: options.data || {},
            header: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + wx.getStorageSync('token')
            },
            success: (res) => {
                if (res.data.code === 0) {
                    resolve(res.data.data);
                } else {
                    wx.showToast({
                        title: res.data.msg,
                        icon: 'none'
                    });
                    reject(res.data);
                }
            },
            fail: (err) => {
                wx.showToast({
                    title: '网络错误',
                    icon: 'none'
                });
                reject(err);
            }
        });
    });
}

module.exports = request;
```

## 部署说明

### 后端部署

#### 生产环境配置

1. 使用 MySQL 替代 SQLite
2. 配置 Nginx 反向代理
3. 使用 Gunicorn 或 uWSGI 作为 WSGI 服务器
4. 配置 HTTPS 证书
5. 设置环境变量

#### Gunicorn 配置示例

```python
# gunicorn.conf.py
bind = '0.0.0.0:5000'
workers = 4
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# 日志
accesslog = '/var/log/gunicorn/access.log'
errorlog = '/var/log/gunicorn/error.log'
loglevel = 'info'
```

#### 启动命令

```bash
gunicorn -c gunicorn.conf.py run:app
```

#### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /uploads {
        alias /path/to/uploads;
    }
}
```

### 小程序发布

1. 代码审核：在微信开发者工具中点击「上传」
2. 填写版本号和更新说明
3. 登录微信公众平台，进入「版本管理」
4. 提交审核
5. 审核通过后点击「发布」

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0.0 | 2024-01-15 | 初始版本，完成基础功能架构 |

## 技术支持

如有问题，请提交 Issue 或联系开发团队。

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 致谢

- Flask 团队提供优秀的 Web 框架
- 微信小程序团队提供开发平台
- 所有贡献者的参与和支持

---

**注意**：本项目仅供学习和交流使用，请勿用于商业用途。如有商业需求，请联系开发者获取授权。
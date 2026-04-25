# 手工爱好者服务平台

## 项目简介

这是一个服务于手工爱好者的微信小程序平台，采用前后端分离架构，帮助客户浏览手作品、下单，同时支持老师展示作品、接单功能。

## 技术栈

- **前端**: 微信小程序原生开发
- **后端**: Python Flask
- **数据库**: SQLite（开发环境）/ MySQL（生产环境）

## 核心功能

### 客户功能
- **作品浏览**：浏览手工作品列表、搜索、分类筛选
- **作品详情**：查看作品详细信息、价格、材料、制作周期
- **下单管理**：创建订单、查看订单列表、订单状态跟踪
- **地址管理**：收货地址的增删改查
- **个人中心**：用户信息管理、收藏夹、订单历史

### 老师功能
- **作品管理**：展示作品、发布新作品、编辑作品信息
- **订单管理**：接收订单、处理订单、更新订单状态
- **个人中心**：老师信息管理、作品管理入口

## 目录结构

```
handicraft-miniprogram/
├── backend/                          # Python Flask后端
│   ├── user-info-api/               # 用户信息API模块
│   ├── role-switch-api/             # 角色切换API模块
│   ├── work-list-api/               # 作品列表API模块
│   ├── work-detail-api/             # 作品详情API模块
│   ├── order-create-api/            # 订单创建API模块
│   ├── order-query-api/             # 订单查询API模块
│   ├── order-operate-api/           # 订单操作API模块
│   ├── teacher-info-api/            # 老师信息API模块
│   ├── common-utils/                # 公共工具模块
│   └── mock-data/                   # 模拟数据模块
│
├── miniprogram/                      # 微信小程序前端
│   ├── address-manage/              # 地址管理页面
│   ├── home-work-show/              # 首页作品展示
│   ├── work-detail/                 # 作品详情页面
│   ├── user-center/                 # 用户中心
│   ├── role-switch/                 # 角色切换页面
│   ├── order-create/                # 订单创建页面
│   ├── order-list/                  # 订单列表页面
│   ├── order-operate/               # 订单操作页面
│   ├── teacher-home/                # 老师主页
│   └── common-utils/                # 公共工具模块
│
├── README.md                         # 项目说明文档
└── .gitignore                        # Git忽略文件
```

## 模块说明

### 后端模块说明

| 模块名称 | 功能描述 |
|---------|---------|
| user-info-api | 用户信息查询、更新等接口 |
| role-switch-api | 客户/老师角色切换接口 |
| work-list-api | 作品列表、搜索、筛选接口 |
| work-detail-api | 作品详情查询、作品发布编辑接口 |
| order-create-api | 订单创建接口 |
| order-query-api | 订单列表查询、订单详情查询接口 |
| order-operate-api | 订单状态更新、订单取消等操作接口 |
| teacher-info-api | 老师信息查询、作品管理接口 |
| common-utils | 公共工具函数、数据库连接、日志等 |
| mock-data | 开发用模拟数据 |

### 前端模块说明

| 模块名称 | 功能描述 |
|---------|---------|
| address-manage | 收货地址的增删改查 |
| home-work-show | 首页作品列表展示、搜索入口 |
| work-detail | 作品详情展示、立即下单入口 |
| user-center | 个人中心、我的订单、收藏夹 |
| role-switch | 客户/老师角色切换界面 |
| order-create | 创建订单、选择地址、确认订单 |
| order-list | 订单列表、按状态筛选 |
| order-operate | 订单详情、订单状态更新操作 |
| teacher-home | 老师主页、作品管理入口、订单管理入口 |
| common-utils | 公共工具函数、API封装、常量定义 |

## 快速开始

### 环境要求

- 微信开发者工具
- Python 3.8+
- pip

### 后端启动

```bash
cd backend
pip install -r requirements.txt
python app.py
```

### 前端启动

1. 使用微信开发者工具打开 `miniprogram` 目录
2. 配置小程序 AppID
3. 编译运行

## 开发规范

- 后端API遵循RESTful风格
- 前端页面采用小程序原生开发规范
- 接口响应格式统一：`{code: 0, msg: "success", data: {}}`

## 许可证

MIT License

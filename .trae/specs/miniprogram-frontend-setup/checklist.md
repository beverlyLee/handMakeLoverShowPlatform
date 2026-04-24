# 手工爱好者展示平台小程序前端 - Verification Checklist

## 工程结构与基础配置验证

- [x] **Checkpoint 1**: `handicraft-miniprogram`目录下存在标准小程序三大入口文件：`app.js`、`app.json`、`app.wxss`
- [x] **Checkpoint 2**: 目录结构完整，包含：`pages/`、`components/`、`utils/`、`assets/`、`styles/`
- [x] **Checkpoint 3**: 微信开发者工具能够正常导入项目并编译，无错误

## 后端对接验证

- [x] **Checkpoint 4**: `utils/request.js`存在，封装了`wx.request`，支持GET/POST/PUT/DELETE
- [x] **Checkpoint 5**: `utils/config.js`存在，配置了API基础URL（开发环境`http://127.0.0.1:5000/api`）
- [x] **Checkpoint 6**: `api/`目录下存在模块接口文件：`auth.js`、`products.js`、`orders.js`、`users.js`、`messages.js`、`favorites.js`、`search.js`
- [x] **Checkpoint 7**: 请求工具自动携带`Authorization`头（从storage读取token）
- [x] **Checkpoint 8**: 调用`request.get('/api/health')`能够正确返回后端响应

## 路由与导航验证

- [x] **Checkpoint 9**: `app.json`中配置了`tabBar`，包含4个Tab（首页、分类/搜索、收藏/购物车、我的）
- [x] **Checkpoint 10**: Tab图标和文字风格统一，使用温暖色系（符合手工主题）
- [x] **Checkpoint 11**: 点击Tab能够正确切换到对应页面
- [x] **Checkpoint 12**: `app.json`的`pages`数组中注册了所有页面路由

## 全局样式与主题验证

- [x] **Checkpoint 13**: `styles/variables.wxss`存在，定义了手工主题色板（暖橙主色、米色辅助色、棕色系文字）
- [x] **Checkpoint 14**: `styles/common.wxss`存在，包含通用样式类（flex布局、文字截断、边距类等）
- [x] **Checkpoint 15**: `app.wxss`中引入了变量和通用样式
- [x] **Checkpoint 16**: 配色方案符合手工主题：温暖、自然、不刺眼

## 工具库验证

- [x] **Checkpoint 17**: `utils/storage.js`存在，封装了`setStorage`、`getStorage`、`removeStorage`
- [x] **Checkpoint 18**: 提供了Token和用户信息的专用存取方法
- [x] **Checkpoint 19**: `utils/format.js`存在，包含价格格式化、日期格式化
- [x] **Checkpoint 20**: `utils/util.js`存在，包含防抖、节流、深拷贝等通用函数

## 通用组件验证

- [x] **Checkpoint 21**: `components/loading/`加载动画组件存在
- [x] **Checkpoint 22**: `components/empty/`空状态组件存在
- [x] **Checkpoint 23**: `components/toast/`提示组件存在
- [x] **Checkpoint 24**: `components/price-tag/`价格标签组件存在
- [x] **Checkpoint 25**: 组件样式符合手工主题风格

## 10个功能模块页面框架验证

### 作品浏览模块
- [x] **Checkpoint 26**: `pages/home/index`首页4个文件存在（js/json/wxml/wxss）
- [x] **Checkpoint 27**: `pages/product-detail/index`作品详情页4个文件存在
- [x] **Checkpoint 28**: 页面已在app.json中注册

### 搜索模块
- [x] **Checkpoint 29**: `pages/search/index`搜索页4个文件存在
- [x] **Checkpoint 30**: `pages/search-result/index`搜索结果页4个文件存在
- [x] **Checkpoint 31**: 页面已在app.json中注册

### 用户认证与个人中心模块
- [x] **Checkpoint 32**: `pages/login/index`登录页4个文件存在
- [x] **Checkpoint 33**: `pages/user-center/index`个人中心页4个文件存在
- [x] **Checkpoint 34**: `pages/profile-edit/index`个人信息编辑页4个文件存在
- [x] **Checkpoint 35**: `pages/favorites/index`我的收藏页4个文件存在
- [x] **Checkpoint 36**: 页面已在app.json中注册

### 订单管理模块
- [x] **Checkpoint 37**: `pages/order-list/index`订单列表页4个文件存在
- [x] **Checkpoint 38**: `pages/order-detail/index`订单详情页4个文件存在
- [x] **Checkpoint 39**: `pages/order-create/index`创建订单页4个文件存在
- [x] **Checkpoint 40**: 页面已在app.json中注册

### 地址管理模块
- [x] **Checkpoint 41**: `pages/address-list/index`地址列表页4个文件存在
- [x] **Checkpoint 42**: `pages/address-edit/index`地址编辑页4个文件存在
- [x] **Checkpoint 43**: 页面已在app.json中注册

### 老师端模块
- [x] **Checkpoint 44**: `pages/teacher-products/index`我的作品管理页4个文件存在
- [x] **Checkpoint 45**: `pages/product-publish/index`作品发布页4个文件存在
- [x] **Checkpoint 46**: `pages/teacher-orders/index`老师订单列表页4个文件存在
- [x] **Checkpoint 47**: `pages/teacher-home/index`老师主页4个文件存在
- [x] **Checkpoint 48**: `pages/role-switch/index`角色切换页4个文件存在
- [x] **Checkpoint 49**: 页面已在app.json中注册

### 消息通知模块
- [x] **Checkpoint 50**: `pages/message-list/index`消息列表页4个文件存在
- [x] **Checkpoint 51**: `pages/message-detail/index`消息详情页4个文件存在
- [x] **Checkpoint 52**: 页面已在app.json中注册

## 业务组件验证（可选P2）

- [ ] **Checkpoint 53**: `components/product-card/`作品卡片组件存在
- [ ] **Checkpoint 54**: `components/nav-header/`自定义导航栏组件存在
- [ ] **Checkpoint 55**: `components/bottom-bar/`底部操作栏组件存在

## 集成测试验证

- [x] **Checkpoint 56**: 微信开发者工具编译无错误
- [x] **Checkpoint 57**: Network面板显示API请求正常发出
- [x] **Checkpoint 58**: 控制台无明显报错
- [x] **Checkpoint 59**: 所有页面能够正常跳转（无"页面不存在"错误）
- [x] **Checkpoint 60**: 本地存储功能正常（Token和用户信息可读写）

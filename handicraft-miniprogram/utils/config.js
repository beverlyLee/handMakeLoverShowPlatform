const config = {
  // 开发环境
  development: {
    baseUrl: 'http://127.0.0.1:5001/api',
    timeout: 10000
  },
  // 生产环境
  production: {
    baseUrl: 'https://api.yourdomain.com/api',
    timeout: 10000
  }
};

// 当前环境
const env = 'development'; // 开发时使用 development，发布时改为 production

module.exports = config[env];

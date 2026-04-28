const config = require('./config');

const DEFAULT_IMAGE_DIR = '/assets/images';
const DEFAULT_IMAGE_NAME = 'default-product';
const DEFAULT_IMAGE_EXT = '.jpg';

const DEFAULT_IMAGE = `${DEFAULT_IMAGE_DIR}/${DEFAULT_IMAGE_NAME}${DEFAULT_IMAGE_EXT}`;

const PLACEHOLDER_IMAGE_KEYWORDS = [
  'picsum.photos',
  'placeholder',
  'generating',
  'loremflickr',
  'placehold',
  'dummyimage',
  'unsplash',
  'lorempixel',
  'fillmurray',
  'placecage',
  'stevensegallery',
  'seed/',
  'refresh',
  'preview',
  'text_to_image',
  'text-to-image',
  'prompt=',
  'image_size='
];

console.log(`默认图片路径: ${DEFAULT_IMAGE}`);
console.log(`提示: 可以修改 DEFAULT_IMAGE_EXT 来使用不同的图片后缀（支持 .jpg, .jpeg, .png, .gif, .webp 等）`);
console.log(`文件名必须是: ${DEFAULT_IMAGE_NAME}（可以带任意支持的后缀）`);

function isPlaceholderImage(url) {
  if (!url) return false;
  
  const lowerUrl = url.toLowerCase();
  return PLACEHOLDER_IMAGE_KEYWORDS.some(keyword => lowerUrl.includes(keyword));
}

function getFullImageUrl(url) {
  
  if (!url) {
    return DEFAULT_IMAGE;
  }
  
  const isPlaceholder = isPlaceholderImage(url);
  
  if (isPlaceholder) {
    return DEFAULT_IMAGE;
  }
  
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url;
  }
  
  if (url.startsWith('/assets/') || url.startsWith('assets/')) {
    return url;
  }
  
  if (url.startsWith('/api/images/')) {
    const baseUrl = config.baseUrl.replace('/api', '');
    const fullUrl = baseUrl + url;
    console.log(`[getFullImageUrl] API 图片路径，转换为: ${fullUrl}`);
    return fullUrl;
  }
  
  if (url.startsWith('/uploads/')) {
    const baseUrl = config.baseUrl.replace('/api', '');
    const fullUrl = baseUrl + '/api/upload' + url;
    console.log(`[getFullImageUrl] Uploads 路径，转换为: ${fullUrl}`);
    return fullUrl;
  }
  
  if (url.startsWith('/')) {
    const baseUrl = config.baseUrl.replace('/api', '');
    const fullUrl = baseUrl + url;
    console.log(`[getFullImageUrl] 其他路径，转换为: ${fullUrl}`);
    return fullUrl;
  }
  
  console.log(`[getFullImageUrl] 未知路径，直接返回: ${url}`);
  return url;
}

function getRelativeImageUrl(url) {
  if (!url) {
    return url;
  }
  
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    return url;
  }
  
  const baseUrl = config.baseUrl.replace('/api', '');
  
  if (url.startsWith(baseUrl)) {
    return url.substring(baseUrl.length);
  }
  
  return url;
}

function processProductImages(product) {
  if (!product) return product;
  
  const processed = { ...product };
  
  if (processed.cover_image) {
    processed.cover_image = getFullImageUrl(processed.cover_image);
  }
  
  if (processed.images && Array.isArray(processed.images)) {
    processed.images = processed.images.map(img => getFullImageUrl(img));
  }
  
  if (!processed.cover_image && processed.images && processed.images.length > 0) {
    processed.cover_image = processed.images[0];
  }
  
  if (!processed.images || processed.images.length === 0) {
    if (processed.cover_image) {
      processed.images = [processed.cover_image];
    } else {
      processed.images = [DEFAULT_IMAGE];
      processed.cover_image = DEFAULT_IMAGE;
    }
  }
  
  return processed;
}

function processTeacherInfo(teacher) {
  if (!teacher) return teacher;
  
  const processed = { ...teacher };
  
  if (processed.user_info && processed.user_info.avatar) {
    processed.user_info.avatar = getFullImageUrl(processed.user_info.avatar);
  }
  
  if (processed.studio_images && Array.isArray(processed.studio_images)) {
    processed.studio_images = processed.studio_images.map(img => getFullImageUrl(img));
  }
  
  if (processed.work_photos && Array.isArray(processed.work_photos)) {
    processed.work_photos = processed.work_photos.map(img => getFullImageUrl(img));
  }
  
  return processed;
}

function processUserInfo(user) {
  if (!user) return user;
  
  const processed = { ...user };
  
  if (processed.avatar) {
    processed.avatar = getFullImageUrl(processed.avatar);
  }
  
  return processed;
}

/**
 * 防抖函数
 * @param {Function} fn - 目标函数
 * @param {number} delay - 延迟时间（ms）
 * @returns {Function} 防抖后的函数
 */
function debounce(fn, delay = 300) {
  let timer = null;
  return function (...args) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      fn.apply(this, args);
    }, delay);
  };
}

/**
 * 节流函数
 * @param {Function} fn - 目标函数
 * @param {number} delay - 间隔时间（ms）
 * @returns {Function} 节流后的函数
 */
function throttle(fn, delay = 300) {
  let lastTime = 0;
  return function (...args) {
    const now = Date.now();
    if (now - lastTime >= delay) {
      lastTime = now;
      fn.apply(this, args);
    }
  };
}

/**
 * 对象深拷贝
 * @param {any} obj - 要拷贝的对象
 * @returns {any} 拷贝后的对象
 */
function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }
  
  if (obj instanceof Date) {
    return new Date(obj.getTime());
  }
  
  if (obj instanceof Array) {
    return obj.map(item => deepClone(item));
  }
  
  if (typeof obj === 'object') {
    const clonedObj = {};
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key]);
      }
    }
    return clonedObj;
  }
  
  return obj;
}

/**
 * 检查值是否为空
 * @param {any} value - 要检查的值
 * @returns {boolean} 是否为空
 */
function isEmpty(value) {
  if (value === null || value === undefined) {
    return true;
  }
  if (typeof value === 'string' && value.trim() === '') {
    return true;
  }
  if (Array.isArray(value) && value.length === 0) {
    return true;
  }
  if (typeof value === 'object' && Object.keys(value).length === 0) {
    return true;
  }
  return false;
}

/**
 * 生成随机字符串
 * @param {number} length - 长度
 * @returns {string} 随机字符串
 */
function randomString(length = 16) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

/**
 * 显示加载提示
 * @param {string} title - 提示文字
 */
function showLoading(title = '加载中...') {
  wx.showLoading({
    title,
    mask: true
  });
}

/**
 * 隐藏加载提示
 */
function hideLoading() {
  wx.hideLoading();
}

/**
 * 显示提示
 * @param {string} title - 提示文字
 * @param {string} icon - 图标类型
 */
function showToast(title, icon = 'none') {
  wx.showToast({
    title,
    icon,
    duration: 2000
  });
}

module.exports = {
  getFullImageUrl,
  getRelativeImageUrl,
  processProductImages,
  processTeacherInfo,
  processUserInfo,
  DEFAULT_IMAGE,
  debounce,
  throttle,
  deepClone,
  isEmpty,
  randomString,
  showLoading,
  hideLoading,
  showToast
};

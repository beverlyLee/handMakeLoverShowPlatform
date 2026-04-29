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
    return fullUrl;
  }
  
  if (url.startsWith('/uploads/')) {
    const baseUrl = config.baseUrl.replace('/api', '');
    const fullUrl = baseUrl + '/api/upload' + url;
    return fullUrl;
  }
  
  if (url.startsWith('/')) {
    const baseUrl = config.baseUrl.replace('/api', '');
    const fullUrl = baseUrl + url;
    return fullUrl;
  }
  
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
  
  if (processed.teacher && processed.teacher.avatar) {
    processed.teacher.avatar = getFullImageUrl(processed.teacher.avatar);
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

/**
 * 安全的日期解析函数，解决 iOS 下日期格式兼容性问题
 * iOS 只支持: "yyyy/MM/dd", "yyyy/MM/dd HH:mm:ss", "yyyy-MM-dd", 
 *             "yyyy-MM-ddTHH:mm:ss", "yyyy-MM-ddTHH:mm:ss+HH:mm"
 * 不支持: "yyyy-MM-dd HH:mm:ss"（带空格的时间格式）
 * @param {string} timeStr - 日期字符串
 * @returns {Date} 日期对象
 */
function safeParseDate(timeStr) {
  if (!timeStr) {
    return new Date(0);
  }

  if (typeof timeStr === 'number') {
    return new Date(timeStr);
  }

  if (timeStr instanceof Date) {
    return timeStr;
  }

  let safeTimeStr = timeStr;

  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(safeTimeStr)) {
    safeTimeStr = safeTimeStr.replace(' ', 'T');
  }

  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(safeTimeStr)) {
    safeTimeStr = safeTimeStr.replace(' ', 'T') + ':00';
  }

  if (/^\d{4}\/\d{2}\/\d{2}/.test(safeTimeStr)) {
    safeTimeStr = safeTimeStr.replace(/\//g, '-');
    if (safeTimeStr.includes(' ')) {
      safeTimeStr = safeTimeStr.replace(' ', 'T');
    }
  }

  const parsedDate = new Date(safeTimeStr);

  if (isNaN(parsedDate.getTime())) {
    console.warn(`[safeParseDate] 无法解析日期: ${timeStr}，使用当前时间`);
    return new Date();
  }

  return parsedDate;
}

/**
 * 格式化相对时间
 * @param {string} timeStr - 日期字符串
 * @returns {string} 格式化后的时间（如：刚刚、5分钟前、昨天等）
 */
function formatRelativeTime(timeStr) {
  if (!timeStr) return '';

  const now = new Date();
  const time = safeParseDate(timeStr);
  const diff = now - time;

  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;

  if (diff < minute) {
    return '刚刚';
  } else if (diff < hour) {
    return `${Math.floor(diff / minute)}分钟前`;
  } else if (diff < day) {
    return `${Math.floor(diff / hour)}小时前`;
  } else if (diff < 7 * day) {
    return `${Math.floor(diff / day)}天前`;
  } else {
    const month = time.getMonth() + 1;
    const date = time.getDate();
    return `${month}月${date}日`;
  }
}

/**
 * 格式化日期时间
 * @param {string} timeStr - 日期字符串
 * @param {string} format - 格式，默认 'YYYY-MM-DD HH:mm:ss'
 * @returns {string} 格式化后的日期时间
 */
function formatDateTime(timeStr, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!timeStr) return '';

  const date = safeParseDate(timeStr);

  if (isNaN(date.getTime())) {
    return '';
  }

  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  const hour = date.getHours().toString().padStart(2, '0');
  const minute = date.getMinutes().toString().padStart(2, '0');
  const second = date.getSeconds().toString().padStart(2, '0');

  let result = format;
  result = result.replace(/YYYY/g, year.toString());
  result = result.replace(/MM/g, month);
  result = result.replace(/DD/g, day);
  result = result.replace(/HH/g, hour);
  result = result.replace(/mm/g, minute);
  result = result.replace(/ss/g, second);

  return result;
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
  showToast,
  safeParseDate,
  formatRelativeTime,
  formatDateTime
};

/**
 * 价格格式化
 * @param {number} price - 价格数值
 * @param {boolean} withSymbol - 是否包含¥符号
 * @returns {string} 格式化后的价格字符串
 */
function price(price, withSymbol = true) {
  if (price === null || price === undefined) {
    return withSymbol ? '¥0.00' : '0.00';
  }
  const formatted = Number(price).toFixed(2);
  return withSymbol ? `¥${formatted}` : formatted;
}

/**
 * 日期格式化
 * @param {Date|string|number} date - 日期
 * @param {string} format - 格式化字符串
 * @returns {string} 格式化后的日期字符串
 */
function date(date, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!date) return '';
  
  const d = new Date(date);
  if (isNaN(d.getTime())) return '';
  
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hour = String(d.getHours()).padStart(2, '0');
  const minute = String(d.getMinutes()).padStart(2, '0');
  const second = String(d.getSeconds()).padStart(2, '0');
  
  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hour)
    .replace('mm', minute)
    .replace('ss', second);
}

/**
 * 相对时间格式化
 * @param {Date|string|number} date - 日期
 * @returns {string} 相对时间（如：刚刚、5分钟前、1小时前、昨天等）
 */
function relativeTime(date) {
  if (!date) return '';
  
  const now = new Date();
  const d = new Date(date);
  const diff = now.getTime() - d.getTime();
  
  const second = 1000;
  const minute = 60 * second;
  const hour = 60 * minute;
  const day = 24 * hour;
  
  if (diff < minute) {
    return '刚刚';
  } else if (diff < hour) {
    return `${Math.floor(diff / minute)}分钟前`;
  } else if (diff < day) {
    return `${Math.floor(diff / hour)}小时前`;
  } else if (diff < 2 * day) {
    return '昨天';
  } else if (diff < 7 * day) {
    return `${Math.floor(diff / day)}天前`;
  } else {
    return date(d, 'MM-DD');
  }
}

/**
 * 数字格式化（如：10000 -> 1万）
 * @param {number} num - 数字
 * @returns {string} 格式化后的字符串
 */
function number(num) {
  if (num === null || num === undefined) return '0';
  if (num < 10000) return String(num);
  if (num < 100000000) return `${(num / 10000).toFixed(1)}万`;
  return `${(num / 100000000).toFixed(1)}亿`;
}

module.exports = {
  price,
  date,
  relativeTime,
  number
};

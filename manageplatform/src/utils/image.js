import config from './config'

const DEFAULT_IMAGE = '/images/default-avatar.png'

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
]

export function isPlaceholderImage(url) {
  if (!url) return false
  
  const lowerUrl = url.toLowerCase()
  return PLACEHOLDER_IMAGE_KEYWORDS.some(keyword => lowerUrl.includes(keyword))
}

export function getFullImageUrl(url) {
  if (!url) {
    return DEFAULT_IMAGE
  }
  
  const isPlaceholder = isPlaceholderImage(url)
  
  if (isPlaceholder) {
    return DEFAULT_IMAGE
  }
  
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  
  if (url.startsWith('/assets/') || url.startsWith('assets/')) {
    return url
  }
  
  if (url.startsWith('/api/images/')) {
    const baseUrl = config.baseUrl || ''
    if (baseUrl && !url.startsWith(baseUrl)) {
      return baseUrl + url
    }
    return url
  }
  
  if (url.startsWith('/uploads/')) {
    const baseUrl = config.baseUrl || ''
    if (baseUrl && !url.startsWith(baseUrl)) {
      return baseUrl + '/api/upload' + url
    }
    return '/api/upload' + url
  }
  
  if (url.startsWith('/')) {
    const baseUrl = config.baseUrl || ''
    if (baseUrl && !url.startsWith(baseUrl)) {
      return baseUrl + url
    }
    return url
  }
  
  return url
}

export function getRelativeImageUrl(url) {
  if (!url) {
    return url
  }
  
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    return url
  }
  
  const baseUrl = config.baseUrl || ''
  
  if (baseUrl && url.startsWith(baseUrl)) {
    return url.substring(baseUrl.length)
  }
  
  return url
}

export function processImageList(images) {
  if (!images || !Array.isArray(images)) {
    return []
  }
  return images.map(img => getFullImageUrl(img))
}

export function processProductImages(product) {
  if (!product) return product
  
  const processed = { ...product }
  
  if (processed.cover_image) {
    processed.cover_image = getFullImageUrl(processed.cover_image)
  }
  
  if (processed.images && Array.isArray(processed.images)) {
    processed.images = processImageList(processed.images)
  }
  
  if (!processed.cover_image && processed.images && processed.images.length > 0) {
    processed.cover_image = processed.images[0]
  }
  
  return processed
}

export function processActivityImages(activity) {
  if (!activity) return activity
  
  const processed = { ...activity }
  
  if (processed.cover_image) {
    processed.cover_image = getFullImageUrl(processed.cover_image)
  }
  
  if (processed.images && Array.isArray(processed.images)) {
    processed.images = processImageList(processed.images)
  }
  
  return processed
}

export function processActivityList(activities) {
  if (!activities || !Array.isArray(activities)) {
    return []
  }
  return activities.map(activity => processActivityImages(activity))
}

export function processProductList(products) {
  if (!products || !Array.isArray(products)) {
    return []
  }
  return products.map(product => processProductImages(product))
}

export default {
  getFullImageUrl,
  getRelativeImageUrl,
  processImageList,
  processProductImages,
  processActivityImages,
  processActivityList,
  processProductList,
  isPlaceholderImage
}

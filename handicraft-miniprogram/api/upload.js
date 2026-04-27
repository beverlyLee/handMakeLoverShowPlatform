const config = require('../utils/config');
const storage = require('../utils/storage');
const { showToast } = require('../utils/util');

function uploadImage(filePath, showLoading = true) {
  if (showLoading) {
    wx.showLoading({
      title: '上传中...',
      mask: true
    });
  }

  return new Promise((resolve, reject) => {
    const token = storage.getToken();
    
    wx.uploadFile({
      url: config.baseUrl + '/api/upload/image',
      filePath: filePath,
      name: 'file',
      header: {
        'Authorization': token ? `Bearer ${token}` : ''
      },
      success: (res) => {
        if (showLoading) {
          wx.hideLoading();
        }
        
        let response;
        try {
          response = JSON.parse(res.data);
        } catch (e) {
          const errorMsg = '上传失败，响应格式错误';
          if (showLoading) {
            showToast(errorMsg);
          }
          reject({ code: -1, msg: errorMsg });
          return;
        }
        
        if (response && response.code === 0) {
          resolve(response.data);
        } else {
          const errorMsg = response.msg || '上传失败';
          if (showLoading) {
            showToast(errorMsg);
          }
          reject({ code: response.code || -1, msg: errorMsg });
        }
      },
      fail: (err) => {
        if (showLoading) {
          wx.hideLoading();
        }
        
        const errorMsg = err.errMsg || '上传失败';
        if (showLoading) {
          showToast('上传失败，请重试');
        }
        
        reject({ code: -1, msg: errorMsg });
      }
    });
  });
}

function uploadImages(filePaths, showLoading = true) {
  if (!filePaths || filePaths.length === 0) {
    return Promise.resolve([]);
  }

  if (showLoading) {
    wx.showLoading({
      title: '上传中...',
      mask: true
    });
  }

  const uploadPromises = filePaths.map(filePath => {
    return uploadImage(filePath, false)
      .then(result => ({
        success: true,
        url: result.url,
        filePath: filePath
      }))
      .catch(error => ({
        success: false,
        error: error.msg,
        filePath: filePath
      }));
  });

  return Promise.all(uploadPromises)
    .then(results => {
      if (showLoading) {
        wx.hideLoading();
      }
      
      const successUrls = results.filter(r => r.success).map(r => r.url);
      const failedCount = results.filter(r => !r.success).length;
      
      if (failedCount > 0) {
        showToast(`上传完成，${failedCount} 张失败`);
      }
      
      return {
        total: results.length,
        success: successUrls.length,
        failed: failedCount,
        urls: successUrls,
        results: results
      };
    });
}

module.exports = {
  uploadImage,
  uploadImages
};

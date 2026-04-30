const { createActivity, getActivityTypes } = require('../../api/activities');
const { uploadImages } = require('../../api/upload');
const { showToast, DEFAULT_IMAGE } = require('../../utils/util');
const { getToken } = require('../../utils/storage');

Page({
  data: {
    craftTypes: [],
    activityTypes: [],

    form: {
      title: '',
      description: '',
      craft_type: '',
      activity_type: '',
      start_time: '',
      end_time: '',
      registration_start_time: '',
      registration_deadline: '',
      location: '',
      address: '',
      city: '',
      price: '',
      original_price: '',
      max_participants: 999,
      images: [],
      cover_image: '',
      tags: []
    },

    coverImage: '',
    imageList: [],

    submitting: false,

    currentDate: '',
    minDate: '',
    maxDate: '',

    showTimePicker: false,
    currentPickerType: '',
    tempDate: '',
    tempTime: '',

    displayStartTime: '',
    displayEndTime: '',
    displayRegistrationStart: '',
    displayRegistrationEnd: '',

    showRangePicker: false,
    rangeStartDate: '',
    rangeEndDate: '',
    rangeStartTime: '',
    rangeEndTime: '',
    rangeStartFull: '',
    rangeEndFull: '',

    displayDateRange: '',

    showRegistrationRangePicker: false,
    registrationRangeStartDate: '',
    registrationRangeEndDate: '',
    registrationRangeStartTime: '',
    registrationRangeEndTime: '',

    displayRegistrationRange: ''
  },

  onLoad() {
    console.log('活动发布页面加载');
    this.initDate();
    this.loadActivityTypes();
  },

  initDate() {
    const now = new Date();
    const year = now.getFullYear();
    const month = (now.getMonth() + 1).toString().padStart(2, '0');
    const day = now.getDate().toString().padStart(2, '0');
    const currentDate = `${year}-${month}-${day}`;
    
    const nextYear = now.getFullYear() + 1;
    const maxDate = `${nextYear}-${month}-${day}`;

    this.setData({
      currentDate,
      minDate: currentDate,
      maxDate: maxDate
    });
  },

  async loadActivityTypes() {
    try {
      const result = await getActivityTypes();
      if (result) {
        this.setData({
          craftTypes: result.craft_types || [],
          activityTypes: result.activity_types || []
        });
      }
    } catch (error) {
      console.error('加载活动类型失败:', error);
    }
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field;
    const value = e.detail.value;
    
    this.setData({
      [`form.${field}`]: value
    });
  },

  onCraftTypeChange(e) {
    const index = e.detail.value;
    const craftType = this.data.craftTypes[index];
    
    this.setData({
      'form.craft_type': craftType
    });
  },

  onActivityTypeChange(e) {
    const index = e.detail.value;
    const activityType = this.data.activityTypes[index];
    
    this.setData({
      'form.activity_type': activityType
    });
  },

  openRangePicker() {
    const now = new Date();
    const year = now.getFullYear();
    const month = (now.getMonth() + 1).toString().padStart(2, '0');
    const day = now.getDate().toString().padStart(2, '0');
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');

    const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);
    const tYear = tomorrow.getFullYear();
    const tMonth = (tomorrow.getMonth() + 1).toString().padStart(2, '0');
    const tDay = tomorrow.getDate().toString().padStart(2, '0');

    this.setData({
      showRangePicker: true,
      rangeStartDate: `${year}-${month}-${day}`,
      rangeEndDate: `${tYear}-${tMonth}-${tDay}`,
      rangeStartTime: `${hours}:${minutes}`,
      rangeEndTime: `${hours}:${minutes}`
    });
  },

  closeRangePicker() {
    this.setData({
      showRangePicker: false
    });
  },

  onRangeStartDateChange(e) {
    const startDate = e.detail.value;
    const { rangeEndDate, rangeStartTime, rangeEndTime } = this.data;
    
    if (startDate > rangeEndDate) {
      this.setData({
        rangeStartDate: startDate,
        rangeEndDate: startDate
      });
    } else {
      this.setData({
        rangeStartDate: startDate
      });
    }
  },

  onRangeEndDateChange(e) {
    const endDate = e.detail.value;
    const { rangeStartDate } = this.data;
    
    if (endDate < rangeStartDate) {
      showToast('结束日期不能早于开始日期');
      return;
    }
    
    this.setData({
      rangeEndDate: endDate
    });
  },

  onRangeStartTimeChange(e) {
    this.setData({
      rangeStartTime: e.detail.value
    });
  },

  onRangeEndTimeChange(e) {
    this.setData({
      rangeEndTime: e.detail.value
    });
  },

  confirmRangePicker() {
    const { rangeStartDate, rangeEndDate, rangeStartTime, rangeEndTime } = this.data;
    
    if (!rangeStartDate) {
      showToast('请选择开始日期');
      return;
    }
    
    if (!rangeEndDate) {
      showToast('请选择结束日期');
      return;
    }
    
    const startFull = `${rangeStartDate} ${rangeStartTime}:00`;
    const endFull = `${rangeEndDate} ${rangeEndTime}:00`;
    
    const displayStart = `${rangeStartDate} ${rangeStartTime}`;
    const displayEnd = `${rangeEndDate} ${rangeEndTime}`;
    
    let displayDateRange = '';
    if (rangeStartDate === rangeEndDate) {
      displayDateRange = `${rangeStartDate} ${rangeStartTime} ~ ${rangeEndTime}`;
    } else {
      displayDateRange = `${displayStart} ~ ${displayEnd}`;
    }

    this.setData({
      showRangePicker: false,
      'form.start_time': startFull,
      'form.end_time': endFull,
      displayStartTime: displayStart,
      displayEndTime: displayEnd,
      displayDateRange: displayDateRange
    });
  },

  openRegistrationRangePicker() {
    const now = new Date();
    const year = now.getFullYear();
    const month = (now.getMonth() + 1).toString().padStart(2, '0');
    const day = now.getDate().toString().padStart(2, '0');
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');

    this.setData({
      showRegistrationRangePicker: true,
      registrationRangeStartDate: `${year}-${month}-${day}`,
      registrationRangeEndDate: `${year}-${month}-${day}`,
      registrationRangeStartTime: `${hours}:${minutes}`,
      registrationRangeEndTime: `${hours}:${minutes}`
    });
  },

  closeRegistrationRangePicker() {
    this.setData({
      showRegistrationRangePicker: false
    });
  },

  onRegistrationRangeStartDateChange(e) {
    const startDate = e.detail.value;
    const { registrationRangeEndDate } = this.data;
    
    if (startDate > registrationRangeEndDate) {
      this.setData({
        registrationRangeStartDate: startDate,
        registrationRangeEndDate: startDate
      });
    } else {
      this.setData({
        registrationRangeStartDate: startDate
      });
    }
  },

  onRegistrationRangeEndDateChange(e) {
    const endDate = e.detail.value;
    const { registrationRangeStartDate } = this.data;
    
    if (endDate < registrationRangeStartDate) {
      showToast('结束日期不能早于开始日期');
      return;
    }
    
    this.setData({
      registrationRangeEndDate: endDate
    });
  },

  onRegistrationRangeStartTimeChange(e) {
    this.setData({
      registrationRangeStartTime: e.detail.value
    });
  },

  onRegistrationRangeEndTimeChange(e) {
    this.setData({
      registrationRangeEndTime: e.detail.value
    });
  },

  confirmRegistrationRangePicker() {
    const { 
      registrationRangeStartDate, 
      registrationRangeEndDate, 
      registrationRangeStartTime, 
      registrationRangeEndTime,
      form
    } = this.data;
    
    if (!registrationRangeStartDate) {
      showToast('请选择报名开始日期');
      return;
    }
    
    if (!registrationRangeEndDate) {
      showToast('请选择报名结束日期');
      return;
    }
    
    if (form.start_time && registrationRangeEndDate > form.start_time.substring(0, 10)) {
      showToast('报名结束时间不能晚于活动开始时间');
      return;
    }
    
    const startFull = `${registrationRangeStartDate} ${registrationRangeStartTime}:00`;
    const endFull = `${registrationRangeEndDate} ${registrationRangeEndTime}:00`;
    
    const displayStart = `${registrationRangeStartDate} ${registrationRangeStartTime}`;
    const displayEnd = `${registrationRangeEndDate} ${registrationRangeEndTime}`;
    
    let displayRegistrationRange = '';
    if (registrationRangeStartDate === registrationRangeEndDate) {
      displayRegistrationRange = `${registrationRangeStartDate} ${registrationRangeStartTime} ~ ${registrationRangeEndTime}`;
    } else {
      displayRegistrationRange = `${displayStart} ~ ${displayEnd}`;
    }

    this.setData({
      showRegistrationRangePicker: false,
      'form.registration_start_time': startFull,
      'form.registration_deadline': endFull,
      displayRegistrationStart: displayStart,
      displayRegistrationEnd: displayEnd,
      displayRegistrationRange: displayRegistrationRange
    });
  },

  openTimePicker(e) {
    const type = e.currentTarget.dataset.type;
    const now = new Date();
    const year = now.getFullYear();
    const month = (now.getMonth() + 1).toString().padStart(2, '0');
    const day = now.getDate().toString().padStart(2, '0');
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');

    this.setData({
      showTimePicker: true,
      currentPickerType: type,
      tempDate: `${year}-${month}-${day}`,
      tempTime: `${hours}:${minutes}`
    });
  },

  closeTimePicker() {
    this.setData({
      showTimePicker: false,
      currentPickerType: '',
      tempDate: '',
      tempTime: ''
    });
  },

  onTempDateChange(e) {
    this.setData({
      tempDate: e.detail.value
    });
  },

  onTempTimeChange(e) {
    this.setData({
      tempTime: e.detail.value
    });
  },

  confirmTimePicker() {
    const { currentPickerType, tempDate, tempTime } = this.data;
    const fullTime = `${tempDate} ${tempTime}:00`;
    const displayTime = `${tempDate} ${tempTime}`;

    const updateData = {
      showTimePicker: false
    };

    if (currentPickerType === 'start') {
      updateData['form.start_time'] = fullTime;
      updateData['displayStartTime'] = displayTime;
    } else if (currentPickerType === 'end') {
      updateData['form.end_time'] = fullTime;
      updateData['displayEndTime'] = displayTime;
    } else if (currentPickerType === 'registration_start') {
      updateData['form.registration_start_time'] = fullTime;
      updateData['displayRegistrationStart'] = displayTime;
    } else if (currentPickerType === 'deadline') {
      updateData['form.registration_deadline'] = fullTime;
      updateData['displayRegistrationEnd'] = displayTime;
    }

    this.setData(updateData);
  },

  chooseCoverImage() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const tempFilePath = res.tempFiles[0].tempFilePath;
        this.setData({
          coverImage: tempFilePath
        });
      }
    });
  },

  chooseImages() {
    const { imageList } = this.data;
    const maxCount = 9 - imageList.length;

    if (maxCount <= 0) {
      showToast('最多上传图片数量已达上限');
      return;
    }

    wx.chooseMedia({
      count: maxCount,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const newImages = res.tempFiles.map(file => file.tempFilePath);
        this.setData({
          imageList: [...imageList, ...newImages]
        });
      }
    });
  },

  removeImage(e) {
    const index = e.currentTarget.dataset.index;
    const { imageList } = this.data;
    
    imageList.splice(index, 1);
    this.setData({ imageList });
  },

  removeCoverImage() {
    this.setData({ coverImage: '' });
  },

  validateForm() {
    const { form } = this.data;

    if (!form.title.trim()) {
      showToast('请输入活动标题');
      return false;
    }

    if (!form.craft_type) {
      showToast('请选择手工种类');
      return false;
    }

    if (!form.activity_type) {
      showToast('请选择活动类型');
      return false;
    }

    if (!form.start_time) {
      showToast('请选择活动时间');
      return false;
    }

    if (!form.registration_deadline) {
      showToast('请选择报名时间');
      return false;
    }

    if (!form.location) {
      showToast('请输入活动地点名称');
      return false;
    }

    if (form.price === '') {
      showToast('请输入活动价格');
      return false;
    }

    return true;
  },

  async submitForm() {
    const token = getToken();
    if (!token) {
      showToast('请先登录');
      return;
    }

    if (!this.validateForm()) {
      return;
    }

    this.setData({ submitting: true });

    try {
      wx.showLoading({ title: '发布中...' });

      const { form, coverImage, imageList } = this.data;

      let uploadedImages = [];
      let uploadedCover = '';

      if (imageList.length > 0) {
        try {
          uploadedImages = await uploadImages(imageList);
        } catch (error) {
          console.error('上传图片失败:', error);
        }
      }

      if (coverImage) {
        try {
          const covers = await uploadImages([coverImage]);
          if (covers && covers.length > 0) {
            uploadedCover = covers[0];
          }
        } catch (error) {
          console.error('上传封面图片失败:', error);
        }
      }

      const submitData = {
        title: form.title.trim(),
        description: form.description.trim(),
        craft_type: form.craft_type,
        activity_type: form.activity_type,
        start_time: form.start_time,
        registration_deadline: form.registration_deadline,
        location: form.location.trim(),
        address: form.address ? form.address.trim() : '',
        city: form.city ? form.city.trim() : '',
        price: parseFloat(form.price) || 0,
        original_price: form.original_price ? parseFloat(form.original_price) : 0,
        max_participants: parseInt(form.max_participants) || 999,
        images: uploadedImages,
        cover_image: uploadedCover
      };

      if (form.end_time) {
        submitData.end_time = form.end_time;
      }

      if (form.registration_start_time) {
        submitData.registration_start_time = form.registration_start_time;
      }

      console.log('提交的活动数据:', submitData);

      const result = await createActivity(submitData);
      
      wx.hideLoading();
      showToast('发布成功', 'success');

      setTimeout(() => {
        wx.navigateBack();
      }, 1500);

    } catch (error) {
      wx.hideLoading();
      console.error('发布活动失败:', error);
      showToast(error.msg || '发布失败，请重试');
      this.setData({ submitting: false });
    }
  }
});

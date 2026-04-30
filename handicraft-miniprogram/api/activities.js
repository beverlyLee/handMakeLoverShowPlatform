const { get, post, put, del } = require('../utils/request');
const { getFullImageUrl, DEFAULT_IMAGE } = require('../utils/util');


function processActivityImages(activity) {
  if (!activity) return activity;
  
  const processed = { ...activity };
  
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


function processActivityList(activities) {
  if (!activities || !Array.isArray(activities)) {
    return [];
  }
  return activities.map(activity => processActivityImages(activity));
}


function getActivityTypes() {
  return get('/activities/types');
}


function getLatestActivities(params = {}) {
  return get('/activities/latest', params).then(result => {
    if (result && Array.isArray(result)) {
      return processActivityList(result);
    }
    return [];
  });
}


function getActivities(params = {}) {
  return get('/activities', params).then(result => {
    if (result && result.list) {
      result.list = processActivityList(result.list);
    }
    return result;
  });
}


function getActivityDetail(activityId) {
  return get(`/activities/${activityId}`).then(result => {
    return processActivityImages(result);
  });
}


function createActivity(data) {
  return post('/activities', data);
}


function updateActivity(activityId, data) {
  return put(`/activities/${activityId}`, data);
}


function deleteActivity(activityId) {
  return del(`/activities/${activityId}`);
}


function registerActivity(activityId, data = {}) {
  return post(`/activities/${activityId}/register`, data);
}


function cancelRegistration(activityId) {
  return del(`/activities/${activityId}/register`);
}


function getMyActivities(params = {}) {
  return get('/activities/my', params).then(result => {
    if (result && result.list) {
      result.list = processActivityList(result.list);
    }
    return result;
  });
}


function getMyRegistrations(params = {}) {
  return get('/activities/my-registrations', params).then(result => {
    if (result && result.list) {
      result.list = result.list.map(item => {
        if (item.activity) {
          item.activity = processActivityImages(item.activity);
        }
        return item;
      });
    }
    return result;
  });
}


module.exports = {
  processActivityImages,
  processActivityList,
  getActivityTypes,
  getLatestActivities,
  getActivities,
  getActivityDetail,
  createActivity,
  updateActivity,
  deleteActivity,
  registerActivity,
  cancelRegistration,
  getMyActivities,
  getMyRegistrations
};

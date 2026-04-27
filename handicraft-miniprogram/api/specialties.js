const { get } = require('../utils/request');

function getSpecialties() {
  return get('/specialties');
}

function getSpecialtiesGrouped() {
  return get('/specialties/grouped');
}

module.exports = {
  getSpecialties,
  getSpecialtiesGrouped
};
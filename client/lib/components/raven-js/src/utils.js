'use strict';

function isObject(what) {
    return typeof what === 'object' && what !== null;
}

// Yanked from https://git.io/vS8DV re-used under CC0
// with some tiny modifications
function isError(value) {
  switch ({}.toString.call(value)) {
    case '[object Error]': return true;
    case '[object Exception]': return true;
    case '[object DOMException]': return true;
    default: return value instanceof Error;
  }
}

module.exports = {
    isObject: isObject,
    isError: isError
};

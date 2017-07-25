/* globals require */

function requireAll (r) { r.keys().forEach(r); }

require('./app/config.module.js');
require('./app/constants.js');

requireAll(require.context('./app/', true, /module\.js$/));
requireAll(
    require.context('./app/', true, /^(?!.*(?:\/constants.js$|webpack.js$|module.js$|spec.js$|mock.js$)).*\.js$/)
);


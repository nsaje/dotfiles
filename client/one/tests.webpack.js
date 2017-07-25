/* globals require */

function requireAll (r) { r.keys().forEach(r); }

require('vendor.webpack.js');
require('app.webpack.js');

requireAll(require.context('./app/test', true, /.js$/));
requireAll(require.context('./app/', true, /spec.js$|mock.js$/));

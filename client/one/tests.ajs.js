require('core-js/es6');

require('./vendor.ajs.js');
require('angular-mocks'); // Should be required after AngularJS

require('./main.ajs.js');

requireAll(require.context('./app/ajs-app/test/', true, /\.js$/));
requireAll(require.context('./app/ajs-app/', true, /spec\.js$|mock\.js$/));

function requireAll (r) { r.keys().forEach(r); }

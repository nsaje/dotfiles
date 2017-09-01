require('jquery');
require('angular');
require('moment');

require('../lib/components/bootstrap/dist/js/bootstrap.js');
require('../lib/components/angular-bootstrap/ui-bootstrap-tpls.js');
require('../lib/components/angular-bootstrap-datetimepicker/src/js/datetimepicker.js');
require('../lib/components/angular-daterangepicker/js/angular-daterangepicker.js');
require('../lib/components/angular-hotkeys/build/hotkeys.js');
require('../lib/components/angular-sanitize/angular-sanitize.js');
require('../lib/components/angular-ui-router/release/angular-ui-router.js');
require('../lib/components/angular-ui-select/dist/select.js');
require('../lib/components/angular-ui-select2/src/select2.js');
require('../lib/components/bootstrap-multiselect/dist/js/bootstrap-multiselect.js');
require('../lib/components/ng-tags-input/ng-tags-input.min.js');
require('../lib/components/select2/select2.js');
require('../lib/components/highcharts-ng/dist/highcharts-ng.js');
require('../lib/components/bootstrap/dist/css/bootstrap.min.css');
require('../lib/components/angular-bootstrap-datetimepicker/src/css/datetimepicker.css');
require('../lib/components/bootstrap-multiselect/dist/css/bootstrap-multiselect.css');
require('../lib/components/angular-ui-select/dist/select.css');
require('../lib/components/select2/select2.css');
require('../lib/components/select2/select2-bootstrap.css');
require('../lib/components/bootstrap-daterangepicker/daterangepicker.css');
require('../lib/components/ng-tags-input/ng-tags-input.css');

// Fixme [Webpack Workaround]: Globals
window.daterangepicker = require('../lib/components/bootstrap-daterangepicker/daterangepicker.js');
window.Highcharts = require('../lib/components/highcharts-release/highcharts.js');

window.Raven = require('raven-js');
var ravenAngular = require('raven-js/plugins/angular');
ravenAngular(window.Raven, angular);
window.Raven.Plugins = {Angular: ravenAngular};

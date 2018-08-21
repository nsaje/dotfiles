var common = require('./config/webpack.common.js');

var appConfig = common.getAppConfig();
if (appConfig.env.prod) {
    module.exports = require('./config/webpack.prod.js');
} else if (appConfig.env.test) {
    module.exports = require('./config/webpack.test.js');
} else {
    module.exports = require('./config/webpack.dev.js');
}

var common = require('./config/webpack.common.js');

var appEnvironment = common.getAppEnvironment();
if (appEnvironment.env.prod) {
    module.exports = require('./config/webpack.prod.js');
} else if (appEnvironment.env.test) {
    module.exports = require('./config/webpack.test.js');
} else {
    module.exports = require('./config/webpack.dev.js');
}

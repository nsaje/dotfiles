var common = require('./config/webpack.common.js');

var buildConfig = common.getBuildConfig();
if (buildConfig.env.prod) {
    module.exports = require('./config/webpack.prod.js');
} else if (buildConfig.env.test) {
    module.exports = require('./config/webpack.test.js');
} else {
    module.exports = require('./config/webpack.dev.js');
}


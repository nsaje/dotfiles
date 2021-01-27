var common = require('./config/webpack.common.js');

var appEnvironment = common.getAppEnvironment();
if (appEnvironment.env.prod) {
    module.exports = require('./config/webpack.prod.js');
} else if (appEnvironment.env.test) {
    module.exports = require('./config/webpack.test.js');
} else if (appEnvironment.env.workerDev) {
    module.exports = require('./config/webpack.worker.dev.js');
} else if (appEnvironment.env.workerProd) {
    module.exports = require('./config/webpack.worker.prod.js');
} else {
    module.exports = require('./config/webpack.dev.js');
}

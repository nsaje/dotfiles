var common = require('./webpack.common.js');
var TerserPlugin = require('terser-webpack-plugin');

var appEnvironment = common.getAppEnvironment();
var configs = [];

var config = generateConfig(appEnvironment);
configs.push(config);

module.exports = configs;

function generateConfig(appEnvironment) {
    var config = common.generateWorkerConfig(appEnvironment);

    config.entry = {
        'zemanta-one.worker': [common.root('./one/main.worker.ts')],
    };

    config.output = {
        path: common.root('./dist/one'),
        publicPath: appEnvironment.staticUrl + '/one/',
        filename: '[name].js',
        sourceMapFilename: '[file].map',
    };

    config.optimization = {
        minimize: true,
        minimizer: [
            new TerserPlugin({
                sourceMap: true,
                terserOptions: {
                    keep_fnames: true,
                    keep_classnames: true,
                },
            }),
        ],
    };

    config.devtool = 'source-map';
    config.mode = 'production';

    return config;
}

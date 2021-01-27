var common = require('./webpack.common.js');
var BundleAnalyzerPlugin = require('webpack-bundle-analyzer')
    .BundleAnalyzerPlugin;

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

    if (appEnvironment.analyze) {
        config.plugins = config.plugins.concat([
            // https://www.npmjs.com/package/webpack-bundle-analyzer
            // Visualize size of webpack output files with an interactive zoomable treemap.
            new BundleAnalyzerPlugin({
                analyzerMode: 'static',
            }),
        ]);
    }

    config.devtool = 'eval-cheap-module-source-map';
    config.mode = 'development';

    return config;
}

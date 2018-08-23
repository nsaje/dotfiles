var common = require('./webpack.common.js');
var merge = require('webpack-merge');
var BundleAnalyzerPlugin = require('webpack-bundle-analyzer')
    .BundleAnalyzerPlugin;

var appConfig = common.getAppConfig();
var configs = [];

var mainConfig = generateMainConfig(appConfig);
configs.push(mainConfig);

var theme = common.getTheme(appConfig.theme);
var styleConfig = generateStyleConfig(appConfig, theme);
configs.push(styleConfig);

module.exports = configs;

function generateMainConfig(appConfig) {
    var config = common.generateMainConfig(appConfig);

    config.entry = {
        'zemanta-one.polyfills': common.root('./one/polyfills.ts'),
        'zemanta-one.lib': common.root('./one/vendor.ts'),
        'zemanta-one': common.root('./one/main.ts'),
    };

    config.output = {
        path: common.root('./dist/one'),
        publicPath: 'one/',
        filename: '[name].js',
        sourceMapFilename: '[file].map',
    };

    // Skip loading styles as they are extracted separately
    config.module.rules.push({
        test: /\.less$/,
        loader: 'null-loader',
    });

    if (appConfig.analyze) {
        config.plugins = config.plugins.concat([
            // https://www.npmjs.com/package/webpack-bundle-analyzer
            // Visualize size of webpack output files with an interactive zoomable treemap.
            new BundleAnalyzerPlugin({
                analyzerMode: 'static',
            }),
        ]);
    }

    config.devServer = {
        contentBase: './',
        stats: 'minimal',
        disableHostCheck: true,
        watchOptions: {
            ignored: /node_modules|.*spec\.js|.*mock\.js|.*spec\.ts|.*mock\.ts|\.DS_Store|\.#.*/,
            aggregateTimeout: 300,
            poll: 1000,
        },
    };

    config.devtool = 'source-map';
    config.mode = 'development';

    return config;
}

function generateStyleConfig(appConfig, theme) {
    var mainConfig = common.generateMainConfig(appConfig);
    var styleConfig = common.generateStyleConfig(theme.name);

    var config = merge.smart(mainConfig, styleConfig);

    config.entry = {
        'zemanta-one': [
            common.root('./one/app/styles/main.less'),
            common.root('./one/main.ts'),
        ],
    };

    config.output = {
        path: common.root('./dist/one'),
        publicPath: 'one/',
    };

    config.devtool = 'source-map';
    config.mode = 'development';

    return config;
}

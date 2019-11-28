var common = require('./webpack.common.js');
var merge = require('webpack-merge');
var BundleAnalyzerPlugin = require('webpack-bundle-analyzer')
    .BundleAnalyzerPlugin;
var ForkTsCheckerWebpackPlugin = require('fork-ts-checker-webpack-plugin');

var appEnvironment = common.getAppEnvironment();
var configs = [];

var mainConfig = generateMainConfig(appEnvironment);
configs.push(mainConfig);

var theme = common.getTheme(appEnvironment.theme);
var styleConfig = generateStyleConfig(appEnvironment, theme);
configs.push(styleConfig);

module.exports = configs;

function generateMainConfig(appEnvironment) {
    var config = common.generateMainConfig(appEnvironment);

    config.entry = {
        'zemanta-one': [
            common.root('./one/polyfills.ts'),
            common.root('./one/vendor.ts'),
            common.root('./one/main.ts'),
        ],
    };

    config.output = {
        path: common.root('./dist/one'),
        publicPath: 'one/',
        filename: '[name].js',
        sourceMapFilename: '[file].map',
    };

    config.optimization = {
        minimize: false,
        splitChunks: {
            cacheGroups: {
                polyfills: {
                    test: /(core-js\/es|core-js\/proposals\/reflect-metadata|zone.js\/dist\/zone)/,
                    chunks: 'all',
                    name: 'zemanta-one.polyfills',
                    priority: 20,
                    enforce: true,
                },
                vendor: {
                    test: /(node_modules|lib\/components)/,
                    chunks: 'all',
                    name: 'zemanta-one.lib',
                    priority: 10,
                    enforce: true,
                },
            },
        },
    };

    // Skip loading styles as they are extracted separately
    config.module.rules.push({
        test: /\.less$/,
        loader: 'null-loader',
    });

    config.plugins = config.plugins.concat([
        // https://github.com/TypeStrong/fork-ts-checker-webpack-plugin
        // Runs typescript type checking in a separate process.
        new ForkTsCheckerWebpackPlugin({checkSyntacticErrors: true}),
    ]);

    if (appEnvironment.analyze) {
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

    config.devtool = 'inline-source-map';
    config.mode = 'development';

    return config;
}

function generateStyleConfig(appEnvironment, theme) {
    var mainConfig = common.generateMainConfig(appEnvironment);
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

    config.devtool = 'none';
    config.mode = 'development';

    return config;
}

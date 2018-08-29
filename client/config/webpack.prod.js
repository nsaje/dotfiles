var webpack = require('webpack');
var common = require('./webpack.common.js');
var merge = require('webpack-merge');
var CopyWebpackPlugin = require('copy-webpack-plugin');
var OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin');
var ParallelUglifyPlugin = require('webpack-parallel-uglify-plugin');
var SentryPlugin = require('webpack-sentry-plugin');

var appEnvironment = common.getAppEnvironment();
var configs = [];

// Main app config
var mainConfig = generateMainConfig(appEnvironment);
configs.push(mainConfig);

// Themes configs
var themes = common.getThemes();
Object.keys(themes).forEach(function(key) {
    var styleConfig = generateStyleConfig(appEnvironment, themes[key]);
    configs.push(styleConfig);
});

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
        minimize: true,
        minimizer: [
            // https://github.com/NMFR/optimize-css-assets-webpack-plugin
            // A Webpack plugin to optimize \ minimize CSS assets.
            new OptimizeCSSAssetsPlugin({}),
        ],
        splitChunks: {
            cacheGroups: {
                polyfills: {
                    test: /(core-js\/es6|core-js\/es7\/reflect|zone.js\/dist\/zone)/,
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
        // https://webpack.js.org/plugins/module-concatenation-plugin/
        // Concatenates the scope of all modules into one closure.
        new webpack.optimize.ModuleConcatenationPlugin(),

        // https://webpack.js.org/plugins/copy-webpack-plugin/
        // Copies individual files or entire directories to the build directory
        new CopyWebpackPlugin([
            {
                from: common.root('./one/images'),
                to: 'images',
            },
            {
                from: common.root('./one/assets'),
                to: 'assets',
            },
        ]),

        // https://github.com/gdborton/webpack-parallel-uglify-plugin
        // A faster uglifyjs plugin.
        new ParallelUglifyPlugin({
            sourceMap: true,
        }),
    ]);

    if (appEnvironment.branchName === 'master') {
        config.plugins = config.plugins.concat([
            // https://github.com/40thieves/webpack-sentry-plugin
            // Webpack plugin to upload source maps to Sentry
            new SentryPlugin({
                release: appEnvironment.buildNumber,
                apiKey: appEnvironment.sentryToken,
                organization: 'zemanta',
                project: 'frontend',
                deleteAfterCompile: true,
                suppressErrors: true,
                filenameTransform: function(filename) {
                    var prefix =
                        '~/build-' + appConfig.buildNumber + '/client/one/';
                    return prefix + filename;
                },
            }),
        ]);
    }

    config.devtool = 'source-map';
    config.mode = 'production';

    return config;
}

function generateStyleConfig(appEnvironment, theme) {
    var mainConfig = common.generateMainConfig(appEnvironment);
    var styleConfig = common.generateStyleConfig(theme.name);

    var config = merge.smart(mainConfig, styleConfig);

    var entryName = 'zemanta-one';
    if (theme !== common.THEMES.one) {
        entryName = entryName + '-' + theme.name;
    }

    config.entry = {};
    config.entry[entryName] = [
        common.root('./one/app/styles/main.less'),
        common.root('./one/main.ts'),
    ];

    config.output = {
        path: common.root('./dist/one'),
        publicPath: 'one/',
    };

    config.optimization = {
        minimize: true,
        minimizer: [
            // https://github.com/NMFR/optimize-css-assets-webpack-plugin
            // A Webpack plugin to optimize \ minimize CSS assets.
            new OptimizeCSSAssetsPlugin({}),
        ],
    };

    config.devtool = 'none';
    config.mode = 'production';

    return config;
}

var common = require('./webpack.common.js');
var merge = require('webpack-merge');
var AngularCompilerPlugin = require('@ngtools/webpack').AngularCompilerPlugin;
var ForkTsCheckerWebpackPlugin = require('fork-ts-checker-webpack-plugin');
var OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin');
var BundleAnalyzerPlugin = require('webpack-bundle-analyzer')
    .BundleAnalyzerPlugin;

var appEnvironment = common.getAppEnvironment();
var configs = [];

var config = generateConfig(appEnvironment);
configs.push(config);

module.exports = configs;

function generateConfig(appEnvironment) {
    var mainConfig = common.generateMainConfig(appEnvironment);
    var styleConfig = common.generateStyleConfig(
        appEnvironment,
        appEnvironment.theme.name
    );

    var config = merge.smart(mainConfig, styleConfig);

    if (appEnvironment.aot) {
        config.entry = {
            'zemanta-one': [
                common.root('./one/app/styles/main.less'),
                common.root('./one/polyfills.ts'),
                common.root('./one/vendor.ts'),
                common.root('./one/main.aot.ts'),
            ],
        };
    } else {
        config.entry = {
            'zemanta-one': [
                common.root('./one/app/styles/main.less'),
                common.root('./one/polyfills.ts'),
                common.root('./one/vendor.ts'),
                common.root('./one/main.jit.ts'),
            ],
        };
    }

    config.output = {
        path: common.root('./dist/one'),
        publicPath: appEnvironment.staticUrl + '/one/',
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

    if (appEnvironment.aot) {
        config.module.rules.push({
            test: /(?:\.ngfactory\.js|\.ngstyle\.js|\.tsx?)$/,
            exclude: /node_modules/,
            loader: '@ngtools/webpack',
        });

        config.plugins = config.plugins.concat([
            // https://www.npmjs.com/package/@ngtools/webpack
            // Webpack plugin that AOT compiles Angular components and modules.
            new AngularCompilerPlugin({
                tsConfigPath: common.root('./tsconfig.aot.json'),
                entryModule: common.root('./one/app/app.module.ts#AppModule'),
            }),
        ]);
    } else {
        config.module.rules.push({
            // Angular TypeScript and template loaders
            test: /\.tsx?$/,
            exclude: /node_modules/,
            use: [
                {
                    loader: 'awesome-typescript-loader',
                    options: {
                        transpileOnly: true,
                        configFileName: 'tsconfig.jit.json',
                    },
                },
                {loader: 'angular2-template-loader'},
            ],
        });

        config.plugins = config.plugins.concat([
            // https://github.com/TypeStrong/fork-ts-checker-webpack-plugin
            // Runs typescript type checking in a separate process.
            new ForkTsCheckerWebpackPlugin(),
        ]);
    }

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
        hot: true,
        disableHostCheck: true,
        watchOptions: {
            ignored: /node_modules|.*spec\.js|.*mock\.js|.*spec\.ts|.*mock\.ts|\.DS_Store|\.#.*/,
            aggregateTimeout: 300,
            poll: 1000,
        },
        headers: {
            'Access-Control-Allow-Origin': '*',
        },
    };

    config.devtool = 'eval';
    config.mode = 'development';

    return config;
}

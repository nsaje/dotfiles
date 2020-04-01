var webpack = require('webpack');
var common = require('./webpack.common.js');
var ForkTsCheckerWebpackPlugin = require('fork-ts-checker-webpack-plugin');

var appEnvironment = common.getAppEnvironment();
var config = common.generateMainConfig(appEnvironment);

config.module.rules = [
    {
        // Angular TypeScript and template loaders
        test: /\.tsx?$/,
        exclude: /node_modules/,
        use: [
            {
                loader: 'awesome-typescript-loader',
                options: {
                    transpileOnly: true,
                    configFileName: 'tsconfig.test.json',
                },
            },
            {loader: 'angular2-template-loader'},
        ],
    },
    {
        // https://github.com/angular/universal-starter/pull/593/commits/644c5f6f28a760f94ef111f5a611e2c9ed679b6a
        // Mark files inside `@angular/core` as using SystemJS style dynamic imports.
        // Removing this will cause deprecation warnings to appear.
        test: /(\\|\/)@angular(\\|\/)core(\\|\/).+\.js$/,
        parser: {system: true},
    },
    {
        test: /\.html$/,
        loader: 'html-loader',
    },
    {
        test: /\.css$/,
        use: 'null-loader',
    },
    {
        test: /\.less$/,
        use: 'null-loader',
    },
    {
        // Workaround: Convert AngularJS to CommonJS module
        test: /angular\.js$/,
        loader: 'exports-loader?angular',
        include: [common.root('./lib/components/angular')],
    },
];

config.plugins.push(
    // https://webpack.js.org/plugins/source-map-dev-tool-plugin/
    // Enables more fine grained control of source map generation.
    new webpack.SourceMapDevToolPlugin({
        filename: null,
        test: /\.(ts|js)($|\?)/i,
    }),

    // https://github.com/TypeStrong/fork-ts-checker-webpack-plugin
    // Runs typescript type checking in a separate process.
    new ForkTsCheckerWebpackPlugin({checkSyntacticErrors: true})
);

config.devtool = 'inline-source-map';
config.mode = 'development';

module.exports = config;

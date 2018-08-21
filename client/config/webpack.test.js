var webpack = require('webpack');
var common = require('./webpack.common.js');

var appConfig = common.getAppConfig();
var config = common.generateMainConfig(appConfig);

config.module.rules = [
    {
        test: /\.tsx?$/,
        loaders: ['awesome-typescript-loader', 'angular2-template-loader'],
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
    })
);

config.devtool = 'inline-source-map';
config.mode = 'development';

module.exports = config;

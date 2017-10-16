var webpack = require('webpack');
var common = require('./webpack.common.js');

var buildConfig = common.getBuildConfig();
var testConfig = common.generateMainConfig(buildConfig);

testConfig.module.rules = [
    {
        test: /\.tsx?$/,
        loaders: [
            'awesome-typescript-loader',
            'angular2-template-loader',
        ],
    }, {
        test: /\.html$/,
        loader: 'html-loader',
    }, {
        test: /\.css$/,
        use: 'null-loader',
    }, {
        test: /\.less$/,
        use: 'null-loader',
    }, {
        // Workaround: Convert AngularJS to CommonJS module
        test: /angular\.js$/, loader: 'exports-loader?angular',
        include: [common.root('./lib/components/angular')]
    },
];

testConfig.plugins.push(
    new webpack.SourceMapDevToolPlugin({
        filename: null,
        test: /\.(ts|js)($|\?)/i,
    })
);

module.exports = testConfig;

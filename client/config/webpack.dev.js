var merge = require('webpack-merge');
var common = require('./webpack.common.js');

var devConfig = {};
var buildConfig = common.getBuildConfig();
var theme = common.getTheme(buildConfig.theme);
var mainConfig = common.generateMainConfig(buildConfig);
var styleConfig = common.generateStyleConfig(theme);

devConfig = merge.smart(mainConfig, styleConfig);

devConfig.entry = {
    'zemanta-one.polyfills': common.root('./one/polyfills.ts'),
    'zemanta-one.lib': common.root('./one/vendor.ts'),
    'zemanta-one': [common.root('./one/app/styles/main.less'), common.root('./one/main.ts')],
};

devConfig.output = {
    path: common.root('./dist/one'),
    publicPath: 'one/',
    filename: '[name].js',
    sourceMapFilename: '[file].map',
};

devConfig.devtool = 'cheap-module-eval-source-map';

devConfig.devServer = {
    contentBase: './',
    stats: 'minimal',
    disableHostCheck: true,
    watchOptions: {
        ignored: /node_modules|.*spec\.js|.*mock\.js|.*spec\.ts|.*mock\.ts|\.DS_Store|\.#.*/,
        aggregateTimeout: 300,
        poll: 1000
    },
};

module.exports = devConfig;

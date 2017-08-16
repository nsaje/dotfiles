var merge = require('webpack-merge');
var common = require('./webpack.common.js');

var testConfig = {};
var buildConfig = common.getBuildConfig();
var theme = common.getTheme();
var mainConfig = common.generateMainConfig(buildConfig);
var styleConfig = common.generateStyleConfig(theme);

testConfig = merge.smart(mainConfig, styleConfig);

testConfig.entry = {
    'zemanta-one.polyfills': common.root('./one/polyfills.ts'),
    'zemanta-one.lib': common.root('./one/vendor.ts'),
    'zemanta-one': [common.root('./one/app/styles/main.less'), common.root('./one/main.ts')],
};

testConfig.output = {
    path: common.root('./dist/one'),
    publicPath: 'one/',
    filename: '[name].js',
    sourceMapFilename: '[file].map',
};

testConfig.devtool = 'cheap-module-eval-source-map';

module.exports = testConfig;

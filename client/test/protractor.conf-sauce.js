var fs = require('fs');
var path = require('path');

// load sauce labs credentials
if (!process.env.SAUCE_USERNAME) {
    if (!fs.existsSync(path.join(__dirname, 'sauce.json'))) {
        console.log('Create a sauce.json with your credentials based on the sauce.json.template file.');
        process.exit(1);
    } else {
        process.env.SAUCE_USERNAME = require('./sauce').username;
        process.env.SAUCE_ACCESS_KEY = require('./sauce').accessKey;
    }
}

// load local config
if (!fs.existsSync(path.join(__dirname, 'protractor.localconf.json'))) {
    console.log('Create a protractor.localconf.json with your local configuration based on the protractor.localconf.json.template file.');
    process.exit(1);
} else {
    localConfig = require('./protractor.localconf.json');
}

exports.config = {
    specs: ['e2e/scenarios.js'],
    rootElement: 'div',
    baseUrl: localConfig.baseUrl, // only works when calling browser.get()

    sauceUser: process.env.SAUCE_USERNAME,
    sauceKey: process.env.SAUCE_ACCESS_KEY,

    onPrepare: function () {
        // handle signin
        browser.driver.get(localConfig.baseUrl + '/signin');
        browser.driver.findElement(By.name('username')).sendKeys('protractor@zemanta.com');
        browser.driver.findElement(By.name('password')).sendKeys('testPr0tr4ct0r');
        browser.driver.findElement(By.id('id_signin_btn')).click();

        browser.driver.sleep(1000);  // prevent Broken Pipe error in Django
    },
    multiCapabilities: [{
        'browserName': 'chrome'
    }, {
        'browserName': 'firefox'
    }],

    framework: 'jasmine',
    jasmineNodeOpts: {
        isVerbose: true,
        showColors: true,
        includeStackTrace: true,
        defaultTimeoutInterval: 60000
    }
};

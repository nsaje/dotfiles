var $driver = require('selenium-webdriver');
const width = 1280;
const height = 960;
//var $browser = new $driver.Builder().usingServer().withCapabilities({ 'browserName': 'firefox' }).build();
//var $browser = new $driver.Builder().usingServer().withCapabilities({'browserName': 'chrome', 'takesScreenshot': true });

let chrome = require('selenium-webdriver/chrome');
let im_driver = new $driver.Builder().forBrowser('chrome')
    .setChromeOptions(
    new chrome.Options()
        .headless()
        .windowSize({ width, height })
    );

var $browser = im_driver.build();

$browser.waitForElement = function (locator, timeout) {
    const DEFAULT_TIMEOUT = 1000
    var timeout = timeout || DEFAULT_TIMEOUT;
    return this.wait($driver.until.elementLocated(locator), timeout);
};



// ------------------------------------------------------------------------------------------------
// ----------------------- CUT HERE(when pasting to NewRelic) -------------------------------------
// ------------------------------------------------------------------------------------------------

/**
* Feel free to explore, or check out the full documentation
* https://docs.newrelic.com/docs/synthetics/new-relic-synthetics/scripting-monitors/writing-scripted-browsers
* for details.
*/

const LOGIN_USERNAME = "<INSERT HERE>";
const LOGIN_PASSWORD = "<INSERT HERE>";

var assert = require('assert');
var urls = [];
/*
- BLACKLIST -
It's used when we deploy z1 which breaks checks for
older versions. In such case we would update this check and
this blacklist old versions.

Blacklist can be purged after TTL of blacklisted Demo
*/

var BLACKLIST = [
    'https://polished-river-9202.demo.zemanta.com/', // serves as an example
    'https://security-check-42941.demo.zemanta.com/', // this is special purpose instance
];

function shuffle(array) {
    var i = 0, j = 0, temp = null;

    for (i = array.length - 1; i > 0; i -= 1) {
        j = Math.floor(Math.random() * (i + 1));
        temp = array[i];
        array[i] = array[j];
        array[j] = temp;
    }
}

$browser.get('https://demohub.demo.zemanta.com/').then(function () {
    $browser.findElements($driver.By.tagName('A')).then(function (elements) {
        var promises = [];
        elements.forEach(function (item) {
            promises.push(item.getAttribute('href').then(function (href) {
                console.log('Considering:', href);
                urls.push(href);
            }));
        });
        return Promise.all(promises);
    });
}).then(function () {
    console.log('URLs:' + urls);
    shuffle(urls);
    call_demo_test(urls, 0);
})
    .finally(function () {
        if (typeof $env !== 'undefined' && $env) {
            console.log('Bye New Relic');
        } else {
            $browser.takeScreenshot().then(
                function (image, err) {
                    console.log("Cheese!");
                    require('fs').writeFile('out-' + Date.now() + '.png', image, 'base64', function (err) {
                        console.log(err);
                    });
                }
            );
            $browser.quit();
        };
    });



function call_demo_test(url_list, idx) {
    MAX_RECURSION_DEPTH = 5;
    if (BLACKLIST.indexOf(url_list[idx]) >= 0) {
        console.log('This URL is BLACKLISTed: ' + url_list[idx]);
        return call_demo_test(url_list, idx + 1)
    }
    if (idx >= MAX_RECURSION_DEPTH || idx >= url_list.length) {
        return
    } else {
        promise = test_demo_url(url_list[idx]).then(
            call_demo_test(url_list, idx + 1)
        );
    }

}

function test_demo_url(loginURL) {
    console.log("Fetching ", loginURL);
    var promises2 = [];
    return $browser.get(loginURL).then(function () {
        var promises = [];
        console.log('>> ', loginURL);
        promises.push($browser.findElement($driver.By.id("id_username")).sendKeys(LOGIN_USERNAME));
        console.log('Found id_username');
        promises.push($browser.findElement($driver.By.id("id_password")).sendKeys(LOGIN_PASSWORD));
        console.log('Found id_password');
        promises.push($browser.findElement($driver.By.id("id_signin_btn")).click());
        console.log('Clicked signin button');
        promises.push($browser.waitForElement($driver.By.css(".zem-header-menu a.dropdown-toggle"), 60000).click());
        console.log('Clicked hamburger dropdown menu');
        Promise.all(promises).then(function () {
            console.log('Proceed to Stage 1');
            promises2.push($browser.getCurrentUrl().then(function (url) {
                console.log('>>>> Stage 1: ', url);
                var pattern = new RegExp(loginURL + 'v2/analytics/accounts');
                assert(pattern.test(url), 'URL: ' + loginURL);
                promises2.push($browser.waitForElement($driver.By.css('div.zem-header-menu__logged-in-user'), 60000).getText().then(function (text) {
                    console.log('>>>> Stage 2: ', text);
                    console.log('>>>>', loginURL, 'done');
                    assert.ok(text.indexOf('regular.user+demo@zemanta.com') != -1, "'regular.user+demo@zemanta.com' not found");
                }));
            }));
        });
        promises2.push($browser.sleep(3000));
        return Promise.all(promises2);
    })
}

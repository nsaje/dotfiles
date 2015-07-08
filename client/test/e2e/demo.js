var nav, chart, tabs,
    config = {
        testAdGroup: 'Best Value for International Travel',
        testCampaign: 'Earned Media Promotion & Retargeting'
    },
    demoLoaded = false,
    window = function (path) {
        return browser.executeScript('return window.' + path + ';');
    },
    Nav = function () {
        this.adGroups = element.all(
            by.repeater('adGroup in campaign.adGroups').column('adGroup.name')
        );
        this.campaigns = element.all(
            by.repeater('campaign in account.campaigns').column('campaign.name')
        );
    },
    Tabs = function () {
        this.adGroup = {
            ads: element(by.cssContainingText('.nav-tabs .tab-title', 'Content Ads')),
            sources: element(by.cssContainingText('.nav-tabs .tab-title', 'Media Sources')),
            settings: element(by.cssContainingText('.nav-tabs .tab-title', 'Settings')),
            agency: element(by.cssContainingText('.nav-tabs .tab-title', 'Agency'))
        };
        this.campaign = {
            adGroups: element(by.cssContainingText('.nav-tabs .tab-title', 'Ad groups')),
            agency: element(by.cssContainingText('.nav-tabs .tab-title', 'Agency')),
            budget: element(by.cssContainingText('.nav-tabs .tab-title', 'Budget'))
        };
    };

function $toFloat(str) {
    return parseFloat(str.substr(1).replace(',', ''));
}

function iterate(fns, done, i) {
    if (i === undefined) { i = 0; };
    if (i >= fns.length) { done(); return; }
    fns[i]().then(function () {
        iterate(fns, done, i+1);
    });
}

beforeEach(function () {
    if (!demoLoaded) {
        demoLoaded = true;
        browser.ignoreSynchronization = true;
        browser.get('/demo_mode');
        browser.driver.sleep(3000).then(function () {
            nav = new Nav();
            tabs = new Tabs();
            browser.ignoreSynchronization = false;
        });
    }
});

describe('Demo loading', function () {
    it('demo should be loaded', function () {
        expect(demoLoaded).toBe(true);
        expect(window('isDemo')).toBe(true);
    });
});

describe('Campaign management', function () {
    var elt = null;
    function newCampaign() {
        element(by.css('#nav div .account-name')).click();
        expect(browser.getLocationAbsUrl()).toMatch(/accounts\/[0-9]+\/campaigns/);
        element(by.cssContainingText('.btn-add', '+ Campaign')).click();
        return browser.driver.sleep(0);
    }

    function renameCampaign() {
        tabs.campaign.agency.click();
        element(by.id('name-input')).isPresent();
        expect(browser.getLocationAbsUrl()).toMatch(/campaigns\/[0-9]+\/agency/);

        element(by.id('name-input')).sendKeys(' 123');
        element(by.cssContainingText('.btn-primary', 'Save')).click();

        expect(
            element(by.cssContainingText('.breadcrumb-container li span',
                                         'New demo campaign')).getText()
        ).toEqual('New demo campaign 123');
        expect(
            element(by.cssContainingText('.campaign-group.list-group-item a',
                                         'New demo campaign')).getText()
        ).toEqual('New demo campaign 123');
        return browser.driver.sleep(0);
    }

    function addAdGroup() {
        element(by.cssContainingText('.btn-add', '+ Ad group')).click();
        return browser.driver.sleep(0).then(function () {
            expect(browser.getLocationAbsUrl()).toMatch(/ad_groups\/[0-9]+\/settings/);
            expect(
                element(by.cssContainingText('.ad-group-item.list-group-item span',
                                             'New demo ad group')).getText()
            ).toEqual('New demo ad group');
        });
        
    }

    function enableAdGroup() {
        element(by.cssContainingText('.btn-success', 'Enabled')).click();

        element(by.css('#nav div .account-name')).click();
        return browser.driver.sleep(0);
    }

    function checkIfPresentInLists() {
        elt = by.cssContainingText('td span a','New demo campaign');
        browser.wait(function () {
            return element(elt).isPresent();
        }, 50000).then(function () {
            expect(element(elt).getText()).toEqual('New demo campaign 123');
            
            element(by.cssContainingText('td span a', 'New demo campaign')).click();

            expect(
                element(by.cssContainingText('td span a', 'New demo')).getText()
            ).toEqual('New demo ad group');
            expect(
                element.all(by.cssContainingText('td span', 'Active')).get(0).getText()
            ).toEqual('Active');
        });
        return browser.driver.sleep(0);
    }

    function selectFirstCampaignBudget() {
        var firstCampaign = element.all(by.css('.campaign-group a.campaign-name')).first();
        firstCampaign.getAttribute('href').then(function (url) {
            firstCampaign.click();
            browser.wait(function () {
                return tabs.campaign.budget.isPresent();
            }).then(function () {
                tabs.campaign.budget.click();
            }, 3500);
        });
        return browser.driver.sleep(0);
    }

    function editCampaignBudget() {
        var deferred = protractor.promise.defer(),
            total = 0;

        function addBudget() {
            element(by.id('manage-budget')).clear().sendKeys('200');
            element(by.cssContainingText('.btn-default', 'Allocate')).click();
            return browser.driver.sleep(0);
        }
        function revokeBudget() {
            element(by.id('manage-budget')).clear().sendKeys('100');
            element(by.cssContainingText('.btn-red', 'Revoke')).click();
            return browser.driver.sleep(0);
        }
        function testBudget() {
            element(by.id('total-budget')).getText().then(function (val) {
                expect($toFloat(val)).toBe(total + 100);
                deferred.fulfill();
            });
            return browser.driver.sleep(0);
        }
        
        element(by.id('total-budget')).getText().then(function (val) {
            total = $toFloat(val);
            addBudget().then(function () {
                revokeBudget().then(testBudget);
            });
        });
        return deferred.promise;
    }
    
    it ('new campaign with a new ad group', function (done) {
        expect(demoLoaded).toBe(true);
        iterate([
            newCampaign,
            renameCampaign,
            tabs.campaign.adGroups.click,
            addAdGroup,
            enableAdGroup,
            checkIfPresentInLists,
        ], done);
    });

    it('allocating budget', function (done) {
        expect(demoLoaded).toBe(true);
        iterate([
            selectFirstCampaignBudget,
            editCampaignBudget
        ], done);
    });
});

describe('Media sources and ads', function () {
    function selectAdGroupWithContentAds() {
        element(by.cssContainingText('#nav .ad-group-name', config.testAdGroup)).click();
        browser.driver.sleep(0).then(function () {
            tabs.adGroup.ads.click();
        });
        return browser.driver.sleep(0);
    }
    function addThreeSources() {
        var deferred = protractor.promise.defer(),
            source = 0,
            sourcesAdded = [],
            setLastPaused = function (source) {
                // TODO: don't know how to test this yet
                deferred.fulfill();
            },
            clickSource = function () {
                element.all(by.css('div.add-source')).get(1).click();
                browser.driver.sleep(0).then(function () {
                    var elt = element.all(by.css('.select2-results .select2-result-label')).first();
                    elt.getText().then(function (val) {
                        sourcesAdded.push(val);
                        elt.click();
                        browser.driver.sleep(0).then(function () {
                            source++;
                            expect(
                                element(by.cssContainingText('.table-container td', val)
                                       ).isPresent()).toBe(true);
                            if (source < 3) {
                                clickSource();
                            } else {
                                setLastPaused(val);
                            }
                        });
                    });
                });
            };
        tabs.adGroup.sources.click();
        browser.driver.sleep(0).then(function () {
            clickSource();
        });
        return deferred.promise;
    }
    function createAdGroup() {
        element(by.cssContainingText('#nav .campaign-name', config.testCampaign)).click();
        tabs.campaign.adGroups.click();
        browser.driver.sleep(0).then(function () {
            element(by.cssContainingText('.btn-add', '+ Ad group')).click();
        });
        return browser.driver.sleep(0);
    }
    function uploadAds() {
        var deferred = protractor.promise.defer(),
            checkAds = function () {
                expect(
                    element.all(by.css('.table-container tbody tr')).count()
                ).toBeGreaterThan(4);
                browser.driver.sleep(0).then(deferred.fulfill);
            };
        tabs.adGroup.ads.click();
        element(by.cssContainingText('.btn-add', '+ Content Ads')).click();
        browser.driver.sleep(0).then(function () {
            element(by.id('display-url-input')).sendKeys('Example.com');
            element(by.id('brand-name-input')).sendKeys('Example Brand');
            element(by.id('call-to-action-input')).sendKeys('Examplify!');
            element(by.id('description-input')).sendKeys('DEMO');
            browser.driver.sleep(0).then(function () {
                element(by.cssContainingText('.btn-add', 'Upload')).click();
                browser.driver.sleep(0).then(checkAds);
            });
        });
        return deferred.promise;
    }
    function uploadNewAds() {
        var deferred = protractor.promise.defer(),
            checkAds = function () {
                expect(
                    element.all(by.css('.table-container tbody tr')).count()
                ).toBeGreaterThan(4);
                browser.driver.sleep(0).then(deferred.fulfill);
            };
        tabs.adGroup.ads.click();
        expect(
            element.all(by.css('.table-container tbody tr')).count()
        ).toBeLessThan(4);
        element(by.cssContainingText('.btn-add', '+ Content Ads')).click();
        browser.driver.sleep(0).then(function () {
            element(by.id('display-url-input')).sendKeys('Example.com');
            element(by.id('brand-name-input')).sendKeys('Example Brand');
            element(by.id('call-to-action-input')).sendKeys('Examplify!');
            element(by.id('description-input')).sendKeys('DEMO');
            browser.driver.sleep(0).then(function () {
                element(by.cssContainingText('.btn-add', 'Upload')).click();
                browser.driver.sleep(0).then(checkAds);
            });
        });
        return deferred.promise;
    }
    it ('adding media sources to ads', function (done) {
        expect(demoLoaded).toBe(true);
        iterate([
            selectAdGroupWithContentAds,
            addThreeSources,
        ], done);
    });

    it ('uploading ads', function (done) {
        expect(demoLoaded).toBe(true);
        iterate([
            createAdGroup,
            uploadNewAds,
            addThreeSources,
        ], done);

        iterate([
            selectAdGroupWithContentAds,
            uploadAds
        ], done);
    });
});


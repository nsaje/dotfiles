var nav, chart, tabs,
    config = {
        testAdGroup1: 'Best Value for International Travel',
        testAdGroup2: '4G LTE',
        testAdGroup3: 'Full Feature audience segment',
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
            settings: element(by.cssContainingText('.nav-tabs .tab-title', 'Settings')),
            budget: element(by.cssContainingText('.nav-tabs .tab-title', 'Budget'))
        };
    };

function $toFloat(str) {
    return parseFloat(str.substr(1).replace(',', ''));
}

function selectCell(parent, i, j, after) {
    after = after ? (' ' + after) : '';
    return element(
        by.css(parent + ' table tbody tr:nth-child(' + i + ') td:nth-child(' + j + ')' + after)
    );
}

function selectCellAll(parent, i, j, after) {
    return element.all(
        by.css(parent + ' table tbody tr:nth-child(' + i + ') td:nth-child(' + j + ') ' + after)
    );
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
    }

    function renameCampaign() {
        tabs.campaign.settings.click();
        element(by.id('name-input')).isPresent();
        expect(browser.getLocationAbsUrl()).toMatch(/campaigns\/[0-9]+\/settings/);

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
    }

    function addAdGroup() {
        element(by.cssContainingText('.btn-add', '+ Ad group')).click();
        expect(browser.getLocationAbsUrl()).toMatch(/ad_groups\/[0-9]+\/settings/);
        expect(
            element(by.cssContainingText('.ad-group-item.list-group-item span',
                                         'New demo ad group')).getText()
        ).toEqual('New demo ad group');
    }

    function enableAdGroup() {
        element(by.cssContainingText('.btn-success', 'Enabled')).click();
        element(by.css('#nav div .account-name')).click();
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
    }

    function editCampaignBudget() {
        var deferred = protractor.promise.defer(),
            total = 0;

        function addBudget() {
            element(by.id('manage-budget')).clear().sendKeys('200');
            element(by.cssContainingText('.btn-default', 'Allocate')).click();
        }
        function revokeBudget() {
            element(by.id('manage-budget')).clear().sendKeys('100');
            element(by.cssContainingText('.btn-red', 'Revoke')).click();
        }
        function testBudget() {
            element(by.id('total-budget')).getText().then(function (val) {
                expect($toFloat(val)).toBe(total + 100);
                deferred.fulfill();
            });
        }
        element(by.id('total-budget')).getText().then(function (val) {
            total = $toFloat(val);
            addBudget();
            revokeBudget();
            testBudget();
        });
    }
    
    it ('new campaign with a new ad group', function () {
        expect(demoLoaded).toBe(true);
        newCampaign();
        renameCampaign();
        tabs.campaign.adGroups.click();
        addAdGroup();
        enableAdGroup();
        checkIfPresentInLists();
    });

    it('allocating budget', function () {
        expect(demoLoaded).toBe(true);
        selectFirstCampaignBudget();
        editCampaignBudget();
    });
});

describe('Media sources and ads', function () {
    function selectAdGroupWithContentAds(i) {
        i = i || 0;
        element(by.cssContainingText('#nav .ad-group-name', {
            0: config.testAdGroup1,
            1: config.testAdGroup2,
            2: config.testAdGroup3
        }[i])).click();
        tabs.adGroup.ads.click();
    }
    function checkSourcesForAds(running, paused) {
        var sep = running && paused ? ' ' : '';
        running = running || '';
        paused = paused || '';
        
        tabs.adGroup.ads.click();
        expect(
            element(by.css('table tbody tr:nth-child(2) td:nth-child(4)')).getText()
        ).toBe(running + sep + paused);
        expect(
            element(by.css('table tbody tr:nth-child(3) td:nth-child(4)')).getText()
        ).toBe(running + sep + paused);
        expect(
            element(by.css('table tbody tr:nth-child(4) td:nth-child(4)')).getText()
        ).toBe(running + sep + paused);
    }
    function addThreeSources() {
        var deferred = protractor.promise.defer(),
            source = 0,
            sourcesAdded = [],
            clickSource = function () {
                element(by.css('div.add-source')).click();
                var elt = element.all(by.css('.add-source-dropdown .select2-results .select2-result-label')).first();
                elt.getText().then(function (val) {
                    sourcesAdded.push(val);
                    elt.click();
                    source++;
                    expect(
                        element(by.cssContainingText('.table-container td', val)).isPresent()
                    ).toBe(true);
                    if (source < 3) {
                        clickSource();
                    } else {
                        deferred.fulfill();
                    }
                });
            };
        tabs.adGroup.sources.click();
        clickSource();
        return deferred.promise;
    }
    function createAdGroup() {
        element(by.cssContainingText('#nav .campaign-name', config.testCampaign)).click();
        tabs.campaign.adGroups.click();
        element(by.cssContainingText('.btn-add', '+ Ad group')).click();
    }
    function uploadAds() {
        tabs.adGroup.ads.click();
        element(by.cssContainingText('.btn-add', '+ Content Ads')).click();
        element(by.id('display-url-input')).sendKeys('Example.com');
        element(by.id('brand-name-input')).sendKeys('Example Brand');
        element(by.id('call-to-action-input')).sendKeys('Examplify!');
        element(by.id('description-input')).sendKeys('DEMO');
        element(by.cssContainingText('.btn-add', 'Upload')).click();
        expect(
            element.all(by.css('.table-container tbody tr')).count()
        ).toBeGreaterThan(4);
    }
    it('adding media sources to ads', function () {
        expect(demoLoaded).toBe(true);
        selectAdGroupWithContentAds(0);

        checkSourcesForAds(0, 4);
        addThreeSources();
        checkSourcesForAds(3, 4);
    });

    it('uploading ads', function () {
        expect(demoLoaded).toBe(true);
        createAdGroup();
        uploadAds();
        checkSourcesForAds(5, 0);
        addThreeSources();
        checkSourcesForAds(8, 0);
        
        selectAdGroupWithContentAds(2);
        uploadAds();
        checkSourcesForAds(0, 4);
    });

    
    it('new ad group sources management', function () {
        var page = '.page-ad-group-sources';
        expect(demoLoaded).toBe(true);
        createAdGroup();
        tabs.adGroup.sources.click();
        expect(
            element.all(by.css(page + ' table tbody tr')).count()
        ).toBeGreaterThan(5);

        expect(
            selectCell(page, 2, 3).getText()
        ).toBe('Outbrain');

        expect(
            selectCell(page, 2, 4).getText()
        ).toBe('Active');

        expect(
            selectCell(page, 2, 5).getText()
        ).toBe('$0.18');

        expect(
            selectCell(page, 2, 6).getText()
        ).toBe('$2,500');

        uploadAds();
        checkSourcesForAds(5, 0);
        tabs.adGroup.sources.click();

        element(by.css('.table tbody tr:nth-child(2) td .zem-state-selector button')).click();
        element(by.css('.table tbody tr:nth-child(2) td .zem-state-selector ul li:nth-child(3) a')).click();

        expect(
            selectCell(page, 2, 4).getText()
        ).toBe('Paused');

        checkSourcesForAds(4, 1);
        tabs.adGroup.sources.click();

        selectCell(page, 3, 5, '.edit-field').click();
        selectCell(page, 3, 5, 'input').clear().sendKeys('0.5').then(function () {
            selectCell(page, 3, 5, '.btn-primary').click();
            expect(
                selectCell(page, 3, 5).getText()
            ).toBe('$0.50');
        });

        selectCell(page, 3, 6, '.edit-field').click();
        selectCell(page, 3, 6, 'input').clear().sendKeys('5555').then(function () {
            selectCell(page, 3, 6, '.btn-primary').click();
            expect(
                selectCell(page, 3, 6).getText()
            ).toBe('$5,555');
        });

        selectCell(page, 3, 6, '.edit-field').click();
        selectCell(page, 3, 6, 'input').clear().sendKeys('6666').then(function () {
            selectCell(page, 3, 6, '.btn-default').click();
            expect(
                selectCell(page, 3, 6).getText()
            ).toBe('$5,555');
        });
    });

    it ('existing ad group sources management', function () {
        expect(demoLoaded).toBe(true);
        element(by.cssContainingText('#nav .ad-group-name', config.testAdGroup2)).click();
        tabs.adGroup.sources.click();
        expect(
            element.all(by.css('.page-ad-group-sources table tbody tr')).count()
        ).toBeGreaterThan(5);

        expect(
            selectCell('.page-ad-group-sources', 2, 3).getText()
        ).toBe('Gravity');

        expect(
            selectCell('.page-ad-group-sources', 3, 3).getText()
        ).toBe('Outbrain');

        expect(
            selectCell('.page-ad-group-sources', 4, 3).getText()
        ).toBe('Yahoo');

        expect(
            selectCell('.page-ad-group-sources', 7, 4).getText()
        ).toBe('Paused');

        element(by.css('.table tbody tr:nth-child(7) td .zem-state-selector button')).click();
        element(by.css('.table tbody tr:nth-child(7) td .zem-state-selector ul li:nth-child(1) a')).click();

        expect(
            selectCell('.page-ad-group-sources', 7, 4).getText()
        ).toBe('Active');

    });

    
});

describe('bulk actions', function () {
    function bulkPause() {
        element(by.css('zem-dropdown > span > .show-rows a')).click();
        element(by.css('#select2-drop ul li:nth-child(1)')).click();
    }
    function bulkResume() {
        element(by.css('zem-dropdown > span > .show-rows a')).click();
        element(by.css('#select2-drop ul li:nth-child(2)')).click();
    }
    function checkRowPaused(row) {
        expect(
            selectCellAll('.page-ad-group-ads-plus', row, 3, 'div button .active-circle-icon').count()
        ).toBe(0);
        expect(
            selectCellAll('.page-ad-group-ads-plus', row, 3, 'div button .pause-icon').count()
        ).toBe(1);
    }
    function checkRowActive(row) {
        expect(
            selectCellAll('.page-ad-group-ads-plus', row, 3, 'div button .active-circle-icon').count()
        ).toBe(1);
        expect(
            selectCellAll('.page-ad-group-ads-plus', row, 3, 'div button .pause-icon').count()
        ).toBe(0);
    }
    
    it('bulk pausing and enabling specific content ads', function () {
        expect(demoLoaded).toBe(true);
        element(by.cssContainingText('#nav .ad-group-name', config.testAdGroup1)).click();
        tabs.adGroup.ads.click();

        // Bulk button disabled and second ad unckecked
        expect(element.all(by.css('zem-dropdown span div.select2-container-disabled')).count()).toBe(1);
        expect(selectCellAll('.page-ad-group-ads-plus', 2, 1, 'input:checked').count()).toBe(0);
        
        // Select first ad
        selectCell('.page-ad-group-ads-plus', 2, 1, 'input').click();

        // Bulk button enabled and ad selected
        expect(element.all(by.css('zem-dropdown span div.select2-container-disabled')).count()).toBe(0);
        expect(selectCellAll('.page-ad-group-ads-plus', 2, 1, 'input:checked').count()).toBe(1);
        
        checkRowActive(2);
        bulkPause();
        checkRowPaused(2);
        bulkResume();
        checkRowActive(2);

        selectCell('.page-ad-group-ads-plus', 2, 1, 'input').click();
        selectCell('.page-ad-group-ads-plus', 3, 1, 'input').click();
        selectCell('.page-ad-group-ads-plus', 4, 1, 'input').click();

        bulkPause();
        checkRowActive(2);
        checkRowPaused(3);
        checkRowPaused(4);

        bulkResume();
        checkRowActive(2);
        checkRowActive(3);
        checkRowActive(4);

        selectCell('.page-ad-group-ads-plus', 3, 1, 'input').click();
        selectCell('.page-ad-group-ads-plus', 4, 1, 'input').click();

        // Bulk button disabled
        expect(element.all(by.css('zem-dropdown span div.select2-container-disabled')).count()).toBe(1);
    });

    it('bulk pausing/enabling all content ads', function () {
        expect(demoLoaded).toBe(true);
        element(by.cssContainingText('#nav .ad-group-name', config.testAdGroup1)).click();
        tabs.adGroup.ads.click();

        
        expect(selectCellAll('.page-ad-group-ads-plus', 2, 1, 'input:checked').count()).toBe(0);
        expect(selectCellAll('.page-ad-group-ads-plus', 3, 1, 'input:checked').count()).toBe(0);
        expect(selectCellAll('.page-ad-group-ads-plus', 4, 1, 'input:checked').count()).toBe(0);
        element(by.id('zem-all-checkbox')).click();
        expect(selectCellAll('.page-ad-group-ads-plus', 2, 1, 'input:checked').count()).toBe(1);
        expect(selectCellAll('.page-ad-group-ads-plus', 3, 1, 'input:checked').count()).toBe(1);
        expect(selectCellAll('.page-ad-group-ads-plus', 4, 1, 'input:checked').count()).toBe(1);

        checkRowActive(2);
        checkRowActive(3);
        checkRowActive(4);
        checkRowActive(5);
        
        bulkPause();
        
        checkRowPaused(2);
        checkRowPaused(3);
        checkRowPaused(4);
        checkRowPaused(5);

        bulkResume();
        
        checkRowActive(2);
        checkRowActive(3);
        checkRowActive(4);
        checkRowActive(5);
        
        element(by.id('zem-all-checkbox')).click();
        expect(selectCellAll('.page-ad-group-ads-plus', 2, 1, 'input:checked').count()).toBe(0);
        expect(selectCellAll('.page-ad-group-ads-plus', 3, 1, 'input:checked').count()).toBe(0);
        expect(selectCellAll('.page-ad-group-ads-plus', 4, 1, 'input:checked').count()).toBe(0);
    });
});

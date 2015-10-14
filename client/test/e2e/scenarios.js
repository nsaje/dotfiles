var Nav = function () {
    this.adGroups = element.all(by.repeater('adGroup in campaign.adGroups').column('adGroup.name'));
    this.campaigns = element.all(by.repeater('campaign in account.campaigns').column('campaign.name'));
};

var Chart = function () {
    this.metric1Select = element(by.css('.select2-container.metric1 .select2-choice'));
    this.metric1SelectOptions = element.all(by.css('.select2-container.metric1 .select2-drop ul.select2-results li'));

    this.metric2Select = element(by.css('.select2-container.metric2 .select2-choice'));
    this.metric2SelectOptions = element.all(by.css('.select2-container.metric2 .select2-drop ul.select2-results li'));

    this.container = element(by.css('.page .section:first-child'));
    this.hideButton = element(by.id('chart-btn'));
};

var Tabs = function () {
    this.adGroup = {
        ads: element(by.cssContainingText('.nav-tabs .tab-title', 'CONTENT ADS')),
        sources: element(by.cssContainingText('.nav-tabs .tab-title', 'MEDIA SOURCES')),
        settings: element(by.cssContainingText('.nav-tabs .tab-title', 'SETTINGS')),
        agency: element(by.cssContainingText('.nav-tabs .tab-title', 'AGENCY'))
    },
    this.campaign = {
        adGroups: element(by.cssContainingText('.nav-tabs .tab-title', 'AD GROUPS')),
        agency: element(by.cssContainingText('.nav-tabs .tab-title', 'AGENCY')),
        budget: element(by.cssContainingText('.nav-tabs .tab-title', 'BUDGET'))
    }
};

var nav = new Nav();
var chart = new Chart();
var tabs = new Tabs();

describe('Ad Groups', function () {
    it('should keep the same tab when switching to another ad group', function () {
        browser.get('/');
        nav.adGroups.first().click();

        expect(browser.getLocationAbsUrl()).toMatch(/ad_groups\/[0-9]+\/ads/);
        expect(nav.adGroups.count()).toBeGreaterThan(1);

        tabs.adGroup.sources.click();
        nav.adGroups.last().click();

        expect(browser.getLocationAbsUrl()).toMatch(/ad_groups\/[0-9]+\/sources/);
    });
});

describe('Campaigns', function () {
    it('should keep the same tab when switching to another campaign', function () {
        browser.get('/');
        nav.campaigns.first().click();

        expect(browser.getLocationAbsUrl()).toMatch(/campaigns\/[0-9]+\/ad_groups/);
        expect(nav.campaigns.count()).toBeGreaterThan(1);

        tabs.campaign.agency.click();
        nav.campaigns.last().click();

        expect(browser.getLocationAbsUrl()).toMatch(/campaigns\/[0-9]+\/agency/);
    });
});

describe('All Accounts', function () {
    describe('Accounts Tab', function () {
        var url = '/all_accounts/accounts'

        beforeEach(function () {
            browser.get(url);
        });

        it('should have a correct title', function () {
            expect(browser.getTitle()).toEqual('All accounts | Zemanta');
        });

        it('should remember selected chart metrics', function () {
            expect(browser.getLocationAbsUrl()).not.toMatch(/chart_metric[1-2]=.+/);

            chart.metric1Select.click();
            chart.metric1SelectOptions.filter(function (el) {
                return el.getText().then(function (text) {
                    return text === 'Clicks';
                });
            }).then(function (els) {
                els[0].click();
            });

            chart.metric2Select.click();
            chart.metric2SelectOptions.filter(function (el) {
                return el.getText().then(function (text) {
                    return text === 'Avg. CPC';
                });
            }).then(function (els) {
                els[0].click();
            });

            expect(browser.getLocationAbsUrl()).toMatch(/chart_metric1=clicks/);
            expect(browser.getLocationAbsUrl()).toMatch(/chart_metric2=cpc/);

            // check if it is correctly loaded from local storage
            browser.get(url);
            expect(chart.metric1Select.getText()).toEqual('Clicks');
            expect(chart.metric2Select.getText()).toEqual('Avg. CPC');
            expect(browser.getLocationAbsUrl()).toMatch(/chart_metric1=clicks/);
            expect(browser.getLocationAbsUrl()).toMatch(/chart_metric2=cpc/);
        });

        it('should toggle the chart when toggle button is clicked', function () {
            chart.hideButton.click();
            expect(chart.container.getCssValue('display')).toEqual('none');

            chart.hideButton.click();
            expect(chart.container.getCssValue('display')).not.toEqual('none');
        });
    });
});

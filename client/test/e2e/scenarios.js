describe('All Accounts', function () {
    describe('Accounts View', function () {
        var AccountsView = function () {
            this.metric1Select = element(by.css('.select2-container.metric1'));
            this.metric1SelectOptions = element.all(by.css('.select2-drop.metric1 ul.select2-results li'));

            this.metric2Select = element(by.css('.select2-container.metric2'));
            this.metric2SelectOptions = element.all(by.css('.select2-drop.metric2 ul.select2-results li'));

            this.chartContainer = element(by.css('.page-all-accounts-accounts .section:first-child'));
            this.chartButton = element(by.id('chart-btn'));

            this.get = function () {
                browser.get('/all_accounts/accounts');
            };
        };
        var accountsView = new AccountsView();

        beforeEach(function () {
            accountsView.get();
        });

        it('should have a correct title', function () {
            expect(browser.getTitle()).toEqual('All accounts | Zemanta');
        });

        it('should remember selected chart metrics', function () {
            expect(browser.getLocationAbsUrl()).not.toMatch(/chart_metric[1-2]=.+/);

            accountsView.metric1Select.click();
            accountsView.metric1SelectOptions.then(function (options) {
                expect(options.length).toBe(3);
                expect(options[1].getText()).toBe('Spend');
                options[1].click();
            });

            accountsView.metric2Select.click();
            accountsView.metric2SelectOptions.then(function (options) {
                expect(options.length).toBe(4);
                expect(options[3].getText()).toBe('Avg. CPC');
                options[3].click();
            });

            expect(browser.getLocationAbsUrl()).toMatch(/chart_metric1=cost/);
            expect(browser.getLocationAbsUrl()).toMatch(/chart_metric2=cpc/);

            // check if it is correctly loaded from local storage
            accountsView.get();
            expect(accountsView.metric1Select.getText()).toEqual('Spend');
            expect(accountsView.metric2Select.getText()).toEqual('Avg. CPC');
            expect(browser.getLocationAbsUrl()).toMatch(/chart_metric1=cost/);
            expect(browser.getLocationAbsUrl()).toMatch(/chart_metric2=cpc/);
        });

        it('should toggle the chart when toggle button is clicked', function () {
            accountsView.chartButton.click();
            expect(accountsView.chartContainer.getCssValue('height')).toEqual('0px');

            accountsView.chartButton.click();
            expect(accountsView.chartContainer.getCssValue('height')).not.toEqual('0px');
        });
    });
});

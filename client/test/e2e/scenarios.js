describe('All Accounts', function () {
    describe('Accounts View', function () {
        var AccountsView = function () {
            this.metric1Select = element(by.css('.select2-container.metric1 .select2-choice'));
            this.metric1SelectOptions = element.all(by.css('.select2-drop.metric1 ul.select2-results li'));

            this.metric2Select = element(by.css('.select2-container.metric2 .select2-choice'));
            this.metric2SelectOptions = element.all(by.css('.select2-drop.metric2 ul.select2-results li'));

            this.chartContainer = element(by.css('.page-all-accounts-accounts .section:first-child'));
            this.chartButton = element(by.id('chart-btn'));

            this.get = function () {
                browser.get('/all_accounts/accounts');
            };
        };
        var view = new AccountsView();

        beforeEach(function () {
            view.get();
        });

        it('should have a correct title', function () {
            expect(browser.getTitle()).toEqual('All accounts | Zemanta');
        });

        it('should remember selected chart metrics', function () {
            expect(browser.getLocationAbsUrl()).not.toMatch(/chart_metric[1-2]=.+/);

            view.metric1Select.click();
            view.metric1SelectOptions.then(function (options) {
                expect(options.length).toBe(3);
                expect(options[0].getText()).toBe('Clicks');
                options[0].click();
            });

            view.metric2Select.click();
            view.metric2SelectOptions.then(function (options) {
                expect(options.length).toBe(4);
                expect(options[3].getText()).toBe('Avg. CPC');
                options[3].click();
            });

            expect(browser.getLocationAbsUrl()).toMatch(/chart_metric1=clicks/);
            expect(browser.getLocationAbsUrl()).toMatch(/chart_metric2=cpc/);

            // check if it is correctly loaded from local storage
            view.get();
            expect(view.metric1Select.getText()).toEqual('Clicks');
            expect(view.metric2Select.getText()).toEqual('Avg. CPC');
            expect(browser.getLocationAbsUrl()).toMatch(/chart_metric1=clicks/);
            expect(browser.getLocationAbsUrl()).toMatch(/chart_metric2=cpc/);
        });

        it('should toggle the chart when toggle button is clicked', function () {
            view.chartButton.click();
            expect(view.chartContainer.getCssValue('height')).toEqual('0px');

            view.chartButton.click();
            expect(view.chartContainer.getCssValue('height')).not.toEqual('0px');
        });
    });
});

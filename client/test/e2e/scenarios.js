describe('Zemanta One', function () {
    it('should have a title', function () {
        browser.get('/all_accounts/accounts');
        expect(browser.getTitle()).toEqual('All accounts | Zemanta');
    });
});

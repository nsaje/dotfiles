describe('Zemanta One', function () {
    it('should have a title', function () {
        browser.get('http://localhost:8000/all_accounts/accounts');
        expect(browser.getTitle()).toEqual('All accounts | Zemanta');
    });
});

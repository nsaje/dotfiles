describe('Zemanta One', function () {
    it('should have a title', function () {
        browser.get('http://localhost:8000/');
        expect(browser.getTitle()).toEqual('Zaaaa');
    });
});

'use strict';

describe('zemUserSettings', function () {
    var zemUserSettings;
    var userSettings;
    var $scope;
    var zemLocalStorageServiceMock;
    var $locationMock;

    beforeEach(function () {
        zemLocalStorageServiceMock = (function () {
            var data = {};

            function get (key, namespace) {
                return data[namespace + key];
            }

            function set (key, value, namespace) {
                data[namespace + key] = value;
            }

            return {
                get: get,
                set: set
            };
        })();

        $locationMock = (function () {
            var data = {};

            function search (key, value) {
                if (key === undefined) {
                    return data;
                }

                data[key] = value;
            }

            return {
                search: search,
                url: function () { return ''; }
            };
        })();

        module('one');

        module(function ($provide) {
            $provide.value('zemLocalStorageService', zemLocalStorageServiceMock);
            $provide.value('$location', $locationMock);
        });

        angular.mock.inject(function ($rootScope, _zemUserSettings_) {
            zemUserSettings = _zemUserSettings_;
            $scope = $rootScope.$new();
        });

        userSettings = zemUserSettings.getInstance($scope, 'test');
    });

    it('returns a new instance every time it is called', function () {
        var anotherUserSettings = zemUserSettings.getInstance($scope, 'test');
        expect(userSettings).not.toBe(anotherUserSettings);
    });

    it('correctly inits a setting that is not in url or local storage', function () {
        $scope.setting = false;
        userSettings.register('setting');

        expect(zemLocalStorageServiceMock.get('setting', 'test')).toBe(undefined);
        expect($locationMock.search()['setting']).toBe(undefined);
    });

    it('correctly inits a setting that is in local storage, but not in url (same as default value)', function () {
        zemLocalStorageServiceMock.set('setting', false, 'test');

        $scope.setting = false;
        userSettings.register('setting');

        expect($scope.setting).toBe(false);
        expect(zemLocalStorageServiceMock.get('setting', 'test')).toBe(false);
        expect($locationMock.search()['setting']).toBe(undefined);
    });

    it('correctly inits a setting that is in local storage, but not in url (different than default value)', function () {
        zemLocalStorageServiceMock.set('setting', true, 'test');

        $scope.setting = false;
        userSettings.register('setting');

        expect($scope.setting).toBe(true);
        expect(zemLocalStorageServiceMock.get('setting', 'test')).toBe(true);
        expect($locationMock.search()['setting']).toBe(undefined);
    });

    it('correctly inits a setting that is in url, but not in local storage (same as default value)', function () {
        $locationMock.search('setting', false);

        $scope.setting = false;
        userSettings.register('setting');

        expect($scope.setting).toBe(false);
        expect(zemLocalStorageServiceMock.get('setting', 'test')).toBe(undefined);
        expect($locationMock.search()['setting']).toBe(false);
    });

    it('correctly inits a setting that is in url, but not in local storage (different than default value)', function () {
        $locationMock.search('setting', true);

        $scope.setting = false;
        userSettings.register('setting');

        expect($scope.setting).toBe(true);
        expect(zemLocalStorageServiceMock.get('setting', 'test')).toBe(undefined);
        expect($locationMock.search()['setting']).toBe(true);
    });

    it('correctly inits a setting that is different in url than it is in local storage', function () {
        $locationMock.search('setting', true);
        zemLocalStorageServiceMock.set('setting', false, 'test');

        $scope.setting = false;
        userSettings.register('setting');

        expect($scope.setting).toBe(true);
        expect(zemLocalStorageServiceMock.get('setting', 'test')).toBe(false);
        expect($locationMock.search()['setting']).toBe(true);
    });

    it('correctly updates registered setting', function () {
        $scope.setting = false;

        userSettings.register('setting');
        $scope.$digest();

        expect($scope.setting).toBe(false);
        expect(zemLocalStorageServiceMock.get('setting', 'test')).toBe(undefined);
        expect($locationMock.search()['setting']).toBe(undefined);

        $scope.setting = true;
        $scope.$digest();

        expect($scope.setting).toBe(true);
        expect(zemLocalStorageServiceMock.get('setting', 'test')).toBe(true);
        expect($locationMock.search()['setting']).toBe(true);
    });

    it('doesn\'t update settings registered without watch', function () {
        $scope.setting = false;

        userSettings.registerWithoutWatch('setting');
        $scope.$digest();

        expect($scope.setting).toBe(false);
        expect(zemLocalStorageServiceMock.get('setting', 'test')).toBe(undefined);
        expect($locationMock.search()['setting']).toBe(undefined);

        $scope.setting = true;
        $scope.$digest();

        expect($scope.setting).toBe(true);
        expect(zemLocalStorageServiceMock.get('setting', 'test')).toBe(undefined);
        expect($locationMock.search()['setting']).toBe(undefined);
    });

    it('removes params from url on state change', function () {
        $scope.setting = false;
        userSettings.register('setting');
        $scope.$digest();

        $scope.setting = true;
        $scope.$digest();
        expect($locationMock.search()['setting']).toBe(true);

        $scope.$broadcast('$stateChangeStart');
        expect($locationMock.search()['setting']).toBe(null);
    });

    it('removes params from url on state change on register without watch', function () {
        $scope.setting = false;
        userSettings.registerWithoutWatch('setting');
        $scope.$digest();

        zemUserSettings.setValue('setting', true, 'test');
        $scope.$digest();
        expect($locationMock.search()['setting']).toBe(true);

        $scope.$broadcast('$stateChangeStart');
        expect($locationMock.search()['setting']).toBe(null);
    });

    it('correctly transforms camel case names to underscore', function () {
        $scope.testSetting = false;
        userSettings.register('testSetting');
        $scope.$digest();

        $scope.testSetting = true;
        $scope.$digest();
        expect($locationMock.search()['test_setting']).toBe(true);
    });
});

'use strict';
/* eslint-disable camelcase */

describe('api', function () {
    var $httpBackend, api;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function (_$httpBackend_, _api_) {
        $httpBackend = _$httpBackend_;
        api = _api_;
    }));

    afterEach(function () {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    describe('demo', function () {
        function objForEach (obj, fun) {
            for (var key in obj) {
                if (obj.hasOwnProperty(key)) {
                    fun.call(obj, obj[key], key);
                }
            }
        }
        function getFunName (fun) {
            var name = /^function\s+([\w\$]+)\s*\(/.exec(fun.toString());
            return name ? name[1] : null;
        }
        it('does not mock api methods if demo is inactive', function () {
            objForEach(api, function (obj, objName) {
                objForEach(obj, function (fun, funName) {
                    expect(getFunName(fun)).not.toBe('demo');
                });
            });
        });
    });
});

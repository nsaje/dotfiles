import {PublisherGroupsEndpoint} from './publisher-groups.endpoint';

describe('PublisherGroupsEndpoint', () => {
    let endpoint: PublisherGroupsEndpoint;

    beforeEach(() => {
        endpoint = new PublisherGroupsEndpoint(undefined);
    });
    it('should convert keys from snake_case to camelCase', () => {
        expect(endpoint.snakePropertyToCamelCase('test')).toEqual('test');
        expect(endpoint.snakePropertyToCamelCase('this_is_a_test')).toEqual(
            'thisIsATest'
        );
    });

    it('should convert objects from snake_case to camelCase', () => {
        expect(endpoint.snakeObjectToCamelCase({test: 123})).toEqual({
            test: 123,
        });
        expect(endpoint.snakeObjectToCamelCase({this_is_a_test: 123})).toEqual({
            thisIsATest: 123,
        });
        expect(endpoint.snakeObjectToCamelCase({test: [1, 2, 3]})).toEqual({
            test: [1, 2, 3],
        });

        expect(
            endpoint.snakeObjectToCamelCase({
                this_is: {
                    a_very: {
                        complex_object: 'some_thing',
                        and_also: ['another', 'thing'],
                    },
                    ok: 1,
                },
            })
        ).toEqual({
            thisIs: {
                aVery: {
                    complexObject: 'some_thing',
                    andAlso: ['another', 'thing'],
                },
                ok: 1,
            },
        });
    });

    it('should convert keys from camelCase to snake_case', () => {
        expect(endpoint.camelPropertyToSnakeCase('test')).toEqual('test');
        expect(endpoint.camelPropertyToSnakeCase('thisIsATest')).toEqual(
            'this_is_a_test'
        );
    });

    it('should convert objects from camelCase to snake_case', () => {
        expect(endpoint.camelObjectToSnakeCase({test: 123})).toEqual({
            test: 123,
        });
        expect(endpoint.camelObjectToSnakeCase({thisIsATest: 123})).toEqual({
            this_is_a_test: 123,
        });
        expect(endpoint.camelObjectToSnakeCase({test: [1, 2, 3]})).toEqual({
            test: [1, 2, 3],
        });

        expect(
            endpoint.camelObjectToSnakeCase({
                thisIs: {
                    aVery: {
                        complexObject: 'some_thing',
                        andAlso: ['another', 'thing'],
                    },
                    ok: 1,
                },
            })
        ).toEqual({
            this_is: {
                a_very: {
                    complex_object: 'some_thing',
                    and_also: ['another', 'thing'],
                },
                ok: 1,
            },
        });
    });
});

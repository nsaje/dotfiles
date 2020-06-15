import * as endpointHelpers from './endpoint.helpers';
import {RequestPayload} from '../types/request-payload';

describe('endpointHelpers', () => {
    const payload: RequestPayload = {
        countries: ['SI', 'IT'],
        publishers: [],
        devices: ['4', '2'],
        sources: [],
    };

    it('should correctly generate request properties', () => {
        const requestProperties = endpointHelpers.buildRequestProperties(
            payload
        );

        expect(requestProperties.method).toEqual('GET');
        expect(requestProperties.params.toString()).toEqual(
            'countries=SI,IT&devices=4,2'
        );
        expect(requestProperties.body).toEqual(null);
    });

    it('should replace URL attributes', () => {
        let request = {
            name: 'test',
            url: '/api/{accountId}/testRequest',
        };

        expect(endpointHelpers.replaceUrl(request, {accountId: '42'})).toEqual({
            name: 'test',
            url: '/api/42/testRequest',
        });

        expect(endpointHelpers.replaceUrl(request, {accountId: 42})).toEqual({
            name: 'test',
            url: '/api/42/testRequest',
        });
        // The original object should be left unchanged
        expect(request).toEqual({
            name: 'test',
            url: '/api/{accountId}/testRequest',
        });

        request = {
            name: 'test',
            url: '/api/accountId/testRequest',
        };

        expect(endpointHelpers.replaceUrl(request, {accountId: '42'})).toEqual({
            name: 'test',
            url: '/api/accountId/testRequest',
        });

        request = {
            name: 'test',
            url: '/api/{xxx}/testRequest',
        };

        expect(endpointHelpers.replaceUrl(request, {yyy: '42'})).toEqual({
            name: 'test',
            url: '/api/{xxx}/testRequest',
        });
    });

    it('should correctly convert any object to FormData', () => {
        const someObject = {
            a: 1,
            b: 'two',
        };

        const formData: FormData = endpointHelpers.convertToFormData(
            someObject
        );

        expect(formData).toBeDefined(); // Unfortunately, we can't check the actual content
    });
});

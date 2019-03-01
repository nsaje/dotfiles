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
});

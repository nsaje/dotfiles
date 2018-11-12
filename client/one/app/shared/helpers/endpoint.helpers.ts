import {HttpParams} from '@angular/common/http';
import {APP_CONFIG} from '../../app.config';
import {RequestPayload} from '../types/request-payload';
import {RequestProperties} from '../types/request-properties';

/**
 * The following function is used to create
 * request properties from the given payload.
 * @param payload
 */
export function buildRequestProperties(
    payload: RequestPayload
): RequestProperties {
    let params = new HttpParams();
    for (const item of Object.keys(payload)) {
        if (payload[item].length) {
            params = params.set(item, payload[item].join());
        }
    }
    if (params.toString().length < APP_CONFIG.maxQueryParamsLength) {
        return {method: 'GET', params: params, body: null};
    } else {
        return {method: 'POST', params: null, body: payload};
    }
}

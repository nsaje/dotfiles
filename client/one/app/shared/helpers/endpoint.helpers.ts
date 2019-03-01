import {HttpParams} from '@angular/common/http';
import {APP_CONFIG} from '../../app.config';
import {RequestPayload} from '../types/request-payload';
import {RequestProperties} from '../types/request-properties';
import {RequestStateUpdater} from '../types/request-state-updater';

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

export function getStoreRequestStateUpdater(store: any): RequestStateUpdater {
    return (requestName, requestState) => {
        store.setState({
            ...store.state,
            requests: {
                ...store.state.requests,
                [requestName]: requestState,
            },
        });
    };
}

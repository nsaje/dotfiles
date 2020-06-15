import {HttpParams} from '@angular/common/http';
import {APP_CONFIG} from '../../app.config';
import {RequestPayload} from '../types/request-payload';
import {RequestProperties} from '../types/request-properties';
import {isDefined} from './common.helpers';
import {HttpRequestInfo} from '../types/http-request-info';

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

export function replaceUrl(
    request: HttpRequestInfo,
    replacements: {[key: string]: string | number}
): HttpRequestInfo {
    let newUrl: string = request.url;
    Object.keys(replacements).forEach(key => {
        newUrl = newUrl.replace('{' + key + '}', replacements[key].toString());
    });

    const newRequest: HttpRequestInfo = {
        ...request,
        url: newUrl,
    };

    return newRequest;
}

export function convertToFormData<T>(object: T): FormData {
    const formData: FormData = new FormData();

    Object.keys(object).forEach(key => {
        const value: any = object[key];
        if (isDefined(value)) {
            formData.append(key, value);
        }
    });

    return formData;
}

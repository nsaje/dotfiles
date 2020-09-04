import {Injectable} from '@angular/core';
import {
    HttpEvent,
    HttpInterceptor,
    HttpHandler,
    HttpRequest,
    HttpResponse,
    HttpParams,
} from '@angular/common/http';
import {Observable} from 'rxjs';
import {map} from 'rxjs/operators';
import * as clone from 'clone';
import * as commonHelpers from '../../shared/helpers/common.helpers';
import * as dateHelpers from '../../shared/helpers/date.helpers';
import {ApiHttpParamEncoder} from '../http/api-http-param-encoder';

@Injectable()
export class ApiConverterHttpInterceptor implements HttpInterceptor {
    intercept(
        request: HttpRequest<any>,
        next: HttpHandler
    ): Observable<HttpEvent<any>> {
        // In order to convert the request body to server format,
        // we need to firstly clone the current body. By cloning
        // the object we prevent to notify the possible subscribers.
        // If the body is of type FormData, it means that it can include
        // a File. In this case we should not modify the content in any way.
        request = request.clone({
            body:
                commonHelpers.isDefined(request.body) &&
                request.body instanceof FormData
                    ? request.body
                    : this.convertBodyToServerFormat(clone(request.body)),
            params: this.replaceHttpParamEncoder(request.params),
        });

        return next.handle(request).pipe(
            map((event: HttpEvent<any>) => {
                if (event instanceof HttpResponse) {
                    event = event.clone({
                        body:
                            commonHelpers.isDefined(event.body) &&
                            event.body instanceof FormData
                                ? event.body
                                : this.convertBodyToClientFormat(
                                      clone(event.body)
                                  ),
                    });
                }
                return event;
            })
        );
    }

    private replaceHttpParamEncoder(requestParams: HttpParams): HttpParams {
        const encoder: ApiHttpParamEncoder = new ApiHttpParamEncoder();
        const paramsObject: {[param: string]: string} = {};
        requestParams.keys().forEach(key => {
            paramsObject[key] = requestParams.get(key);
        });

        return new HttpParams({encoder, fromObject: paramsObject});
    }

    private convertBodyToServerFormat(body: any): any {
        if (!commonHelpers.isDefined(body)) {
            return body;
        }
        if (typeof body !== 'object') {
            return body;
        }

        for (const key of Object.keys(body)) {
            const value = body[key];
            // add converters here
            if (value instanceof Date) {
                body[key] = dateHelpers.convertDateToString(value);
            } else if (typeof value === 'object') {
                body[key] = this.convertBodyToServerFormat(value);
            }
        }

        return body;
    }

    private convertBodyToClientFormat(body: any) {
        if (!commonHelpers.isDefined(body)) {
            return body;
        }
        if (typeof body !== 'object') {
            return body;
        }

        for (const key of Object.keys(body)) {
            const value = body[key];
            // add converters here
            if (typeof value === 'string') {
                // add string converters
                if (dateHelpers.canConvertStringToDate(value)) {
                    body[key] = dateHelpers.convertStringToDate(value);
                }
            } else if (typeof value === 'object') {
                body[key] = this.convertBodyToClientFormat(value);
            }
        }

        return body;
    }
}

import {Injectable} from '@angular/core';
import {
    HttpEvent,
    HttpInterceptor,
    HttpHandler,
    HttpRequest,
    HttpResponse,
} from '@angular/common/http';
import {Observable} from 'rxjs';
import {map} from 'rxjs/operators';
import * as clone from 'clone';
import * as commonHelpers from '../../shared/helpers/common.helpers';
import * as dateHelpers from '../../shared/helpers/date.helpers';

@Injectable()
export class ApiConverterHttpInterceptor implements HttpInterceptor {
    intercept(
        request: HttpRequest<any>,
        next: HttpHandler
    ): Observable<HttpEvent<any>> {
        request = request.clone({
            body: this.convertBodyToServerFormat(clone(request.body)),
        });
        return next.handle(request).pipe(
            map((event: HttpEvent<any>) => {
                if (event instanceof HttpResponse) {
                    event = event.clone({
                        body: this.convertBodyToClientFormat(clone(event.body)),
                    });
                }
                return event;
            })
        );
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

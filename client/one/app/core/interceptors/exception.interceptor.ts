import {Injectable} from '@angular/core';
import {
    HttpEvent,
    HttpInterceptor,
    HttpHandler,
    HttpRequest,
    HttpErrorResponse,
} from '@angular/common/http';
import {iif, MonoTypeOperatorFunction, Observable, of, throwError} from 'rxjs';
import {catchError, concatMap, delay, retryWhen} from 'rxjs/operators';
import {ExceptionHandlerService} from '../exception-handler/services/exception-handler.service';
import {HttpException} from '../exception-handler/types/http-exception';
import {isDefined} from '../../shared/helpers/common.helpers';

@Injectable()
export class ExceptionHttpInterceptor implements HttpInterceptor {
    private retryRequestIfNecessary: MonoTypeOperatorFunction<
        HttpEvent<any>
    > = retryWhen(responses =>
        responses.pipe(
            concatMap((response, previousAttempts) =>
                iif(
                    () =>
                        this.exceptionHandlerService.shouldRetryRequest(
                            this.formatException(response),
                            previousAttempts
                        ),
                    // Trigger a repeated request after a set timeout
                    of(response).pipe(
                        delay(
                            this.exceptionHandlerService.getRequestRetryTimeout()
                        )
                    ),
                    // else
                    throwError(response)
                )
            )
        )
    );

    constructor(private exceptionHandlerService: ExceptionHandlerService) {}

    intercept(
        request: HttpRequest<any>,
        next: HttpHandler
    ): Observable<HttpEvent<any>> {
        return next.handle(request).pipe(
            this.retryRequestIfNecessary,
            catchError(
                (
                    response: HttpErrorResponse,
                    event: Observable<HttpEvent<any>>
                ) => {
                    // We did not retry => handle exception and cancel request
                    this.exceptionHandlerService.handleHttpException(
                        this.formatException(response)
                    );
                    return throwError(response);
                }
            )
        );
    }

    private formatException(response: HttpErrorResponse): HttpException {
        const errorData: any = response.error;
        let message: string;
        let errorCode: string;
        if (isDefined(errorData)) {
            message = errorData.details || errorData.message;
            errorCode = errorData.errorCode || errorData.error_code;
        }
        const exception: HttpException = {
            message: message,
            errorCode: errorCode,
            headers: (key: string) => response.headers.get(key),
            status: response.status,
        };

        return exception;
    }
}

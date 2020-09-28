import {Injectable, Inject} from '@angular/core';
import {downgradeInjectable} from '@angular/upgrade/static';
import {APP_CONFIG} from '../../../app.config';
import {NotificationService} from '../../notification/services/notification.service';
import {isDefined} from '../../../shared/helpers/common.helpers';
import {HttpException} from '../types/http-exception';
import * as arrayHelpers from '../../../shared/helpers/array.helpers';

@Injectable()
export class ExceptionHandlerService {
    constructor(private notificationService: NotificationService) {}

    handleHttpException(exception: HttpException) {
        if (this.shouldShowErrorMessage(exception)) {
            const exceptionInfos: string[] = this.getExceptionInfos(exception);
            if (!arrayHelpers.isEmpty(exceptionInfos)) {
                this.notificationService.error(exceptionInfos.join('<br>'));
            }
        }
    }

    shouldRetryRequest(
        exception: HttpException,
        previousRetries: number | undefined
    ): boolean {
        const nextRetryNumber: number = (previousRetries || 0) + 1;
        return (
            nextRetryNumber < APP_CONFIG.maxRequestRetries &&
            APP_CONFIG.httpStatusCodesForRequestRetry.includes(exception.status)
        );
    }

    getRequestRetryTimeout(): number {
        return APP_CONFIG.requestRetryTimeout;
    }

    private shouldShowErrorMessage(exception: HttpException) {
        return (
            (this.isServerErrorHttpStatusCode(exception.status) ||
                this.isNotFoundHttpStatusCode(exception.status)) &&
            this.shouldShowErrorForHttpMethod(exception.method) &&
            this.shouldShowErrorForUrl(exception.url)
        );
    }

    private isServerErrorHttpStatusCode(httpStatus: number): boolean {
        return isDefined(httpStatus) && httpStatus >= 500 && httpStatus <= 599;
    }

    private isNotFoundHttpStatusCode(httpStatus: number): boolean {
        return (
            (isDefined(httpStatus) && httpStatus === 404) ||
            (isDefined(httpStatus) && httpStatus === 403)
        );
    }

    private shouldShowErrorForHttpMethod(httpMethod: string): boolean {
        if (
            isDefined(httpMethod) &&
            isDefined(APP_CONFIG.httpErrorPopupIncludeHttpMethods)
        ) {
            return APP_CONFIG.httpErrorPopupIncludeHttpMethods.includes(
                httpMethod
            );
        } else {
            return true;
        }
    }

    private shouldShowErrorForUrl(url: string): boolean {
        if (
            isDefined(url) &&
            isDefined(APP_CONFIG.httpErrorPopupExcludeUrlRegexes)
        ) {
            const urlExcluded: boolean = APP_CONFIG.httpErrorPopupExcludeUrlRegexes.some(
                regex => regex.test(url)
            );
            return !urlExcluded;
        } else {
            return true;
        }
    }

    private getExceptionInfos(exception: HttpException): string[] {
        const infos: string[] = [];
        this.appendIfDefined('Trace ID', this.getTraceId(exception), infos);
        this.appendIfDefined('Error code', exception.errorCode, infos);
        this.appendIfDefined('Message', exception.message, infos);

        return infos;
    }

    private appendIfDefined(
        key: string,
        value: string | undefined,
        array: string[]
    ) {
        if (isDefined(value)) {
            array.push(`${key}: ${value}`);
        }
    }

    private getTraceId(exception: HttpException): string | undefined {
        return isDefined(exception.headers)
            ? exception.headers('X_Z1_TRACE_ID')
            : undefined;
    }
}

declare var angular: angular.IAngularStatic;
angular
    .module('one.downgraded')
    .factory(
        'zemExceptionHandlerService',
        downgradeInjectable(ExceptionHandlerService)
    );

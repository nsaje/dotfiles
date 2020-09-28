import {HttpException} from '../types/http-exception';
import {APP_CONFIG} from '../../../app.config';
import {ExceptionHandlerService} from './exception-handler.service';
import {NotificationService} from '../../notification/services/notification.service';

describe('ExceptionHandlerService', () => {
    let service: ExceptionHandlerService;
    let notificationServiceStub: jasmine.SpyObj<NotificationService>;
    let testException: HttpException;

    beforeEach(() => {
        APP_CONFIG.requestRetryTimeout = 500;
        APP_CONFIG.maxRequestRetries = 3;
        APP_CONFIG.httpStatusCodesForRequestRetry = [504];
        APP_CONFIG.httpErrorPopupIncludeHttpMethods = ['PUT', 'POST'];
        APP_CONFIG.httpErrorPopupExcludeUrlRegexes = [/.*(\/breakdown\/).*/];

        testException = {
            message: 'An error occured',
            errorCode: 'TestError',
            headers: (key: string) => 'a-dummy-trace-id',
            status: 504,
            method: 'POST',
            url: 'api/ad_groups/1234/alerts/',
        };

        notificationServiceStub = jasmine.createSpyObj(
            NotificationService.name,
            ['error']
        );

        service = new ExceptionHandlerService(notificationServiceStub);
    });

    it('should retry request if retry count is below the max and the status is correct', () => {
        expect(service.shouldRetryRequest(testException, undefined)).toBeTrue();
        expect(service.shouldRetryRequest(testException, 0)).toBeTrue();
    });

    it('should not retry request if number of requests has been exceeded', () => {
        expect(service.shouldRetryRequest(testException, 2)).toBeFalse();
    });

    it('should not retry request if HTTP status code is incorrect', () => {
        testException.status = 403;
        expect(service.shouldRetryRequest(testException, 0)).toBeFalse();
    });

    it('should show error popup containing the appropriate information', () => {
        service.handleHttpException(testException);

        expect(notificationServiceStub.error).toHaveBeenCalledWith(
            'Trace ID: a-dummy-trace-id<br>Error code: TestError<br>Message: An error occured'
        );
    });

    it("should not show an error popup if it can't find any information to display", () => {
        const weirdException = {
            status: 504,
            method: 'POST',
            url: 'api/ad_groups/1234/alerts/',
        };
        service.handleHttpException(<HttpException>weirdException);

        expect(notificationServiceStub.error).not.toHaveBeenCalled();
    });

    it('should not show an error popup if the HTTP method is not correct', () => {
        testException.method = 'GET';
        service.handleHttpException(testException);

        expect(notificationServiceStub.error).not.toHaveBeenCalled();
    });

    it('should not show an error popup if the URL is excluded', () => {
        testException.url = '/api/all_accounts/breakdown/account/';
        service.handleHttpException(testException);

        expect(notificationServiceStub.error).not.toHaveBeenCalled();
    });
});

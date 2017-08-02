import {ErrorHandler} from '@angular/core';

export class RavenErrorHandler implements ErrorHandler {
    handleError (error: Error): void {
        (<any>window).Raven.captureException(error); // tslint:disable-line
    }
}

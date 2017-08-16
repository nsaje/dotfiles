import {APP_CONFIG} from '../config/app.config';
import {ErrorHandler} from '@angular/core';

export class RavenErrorHandler extends ErrorHandler {
    constructor () {
        super();
    }

    handleError (error: Error): void {
        if (APP_CONFIG.env.prod) {
            (<any>window).Raven.captureException(error); // tslint:disable-line
        } else {
            super.handleError(error);
        }
    }
}

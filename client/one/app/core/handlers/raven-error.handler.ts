import {ErrorHandler} from '@angular/core';
import {APP_CONFIG} from '../../app.config';

export class RavenErrorHandler extends ErrorHandler {
    constructor() {
        super();
    }

    handleError(error: any): void {
        // tslint:disable-line
        super.handleError(error);
        if (APP_CONFIG.env.prod) {
            (<any>window).Raven.captureException(error.originalError || error); // tslint:disable-line
        }
    }
}

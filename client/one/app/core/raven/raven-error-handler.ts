import * as Raven from 'raven-js';
import {ErrorHandler} from '@angular/core';

export class RavenErrorHandler extends ErrorHandler {
    constructor () {
        super();
    }

    handleError (error: Error): void {
        super.handleError(error);
        Raven.captureException(error);
    }
}

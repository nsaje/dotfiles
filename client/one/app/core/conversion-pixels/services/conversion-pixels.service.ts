import {Injectable} from '@angular/core';
import {ConversionPixelsEndpoint} from './conversion-pixels.endpoint';
import {ConversionPixel} from '../types/conversion-pixel';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable} from 'rxjs';
import * as commonHelpers from '../../../shared/helpers/common.helpers';

@Injectable()
export class ConversionPixelsService {
    constructor(private endpoint: ConversionPixelsEndpoint) {}

    list(
        accountId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<ConversionPixel[]> {
        return this.endpoint.list(accountId, requestStateUpdater);
    }

    create(
        accountId: string,
        conversionPixelName: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<ConversionPixel> {
        return this.endpoint.create(
            accountId,
            conversionPixelName,
            requestStateUpdater
        );
    }

    edit(
        conversionPixel: ConversionPixel,
        requestStateUpdater: RequestStateUpdater
    ): Observable<ConversionPixel> {
        return this.endpoint.edit(conversionPixel, requestStateUpdater);
    }
}

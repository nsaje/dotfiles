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

    save(
        conversionPixel: ConversionPixel,
        requestStateUpdater: RequestStateUpdater
    ): Observable<ConversionPixel> {
        if (!commonHelpers.isDefined(conversionPixel.id)) {
            return this.create(conversionPixel, requestStateUpdater);
        }
        return this.edit(conversionPixel, requestStateUpdater);
    }

    private create(
        conversionPixel: ConversionPixel,
        requestStateUpdater: RequestStateUpdater
    ): Observable<ConversionPixel> {
        return this.endpoint.create(conversionPixel, requestStateUpdater);
    }

    private edit(
        conversionPixel: ConversionPixel,
        requestStateUpdater: RequestStateUpdater
    ): Observable<ConversionPixel> {
        return this.endpoint.edit(conversionPixel, requestStateUpdater);
    }
}

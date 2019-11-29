import {Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {BidModifiersEndpoint} from './bid-modifiers.endpoint';
import {BidModifier} from '../types/bid-modifier';
import {BidModifierUploadSummary} from '../types/bid-modifier-upload-summary';
import {RequestStateUpdater} from 'one/app/shared/types/request-state-updater';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import {Breakdown} from '../../../app.constants';

@Injectable()
export class BidModifiersService {
    constructor(private endpoint: BidModifiersEndpoint) {}

    save(
        adGroupId: number,
        bidModifier: BidModifier,
        requestStateUpdater: RequestStateUpdater
    ): Observable<BidModifier> {
        if (!commonHelpers.isDefined(bidModifier.id)) {
            return this.endpoint.create(
                adGroupId,
                bidModifier,
                requestStateUpdater
            );
        }
        return this.endpoint.edit(adGroupId, bidModifier, requestStateUpdater);
    }

    importFromFile(
        adGroupId: number,
        breakdown: Breakdown,
        file: File,
        requestStateUpdater: RequestStateUpdater
    ): Observable<BidModifierUploadSummary> {
        return this.endpoint.upload(
            adGroupId,
            breakdown,
            file,
            requestStateUpdater
        );
    }

    validateImportFile(
        adGroupId: number,
        breakdown: Breakdown,
        file: File,
        requestStateUpdater: RequestStateUpdater
    ): Observable<BidModifierUploadSummary> {
        return this.endpoint.validateUpload(
            adGroupId,
            breakdown,
            file,
            requestStateUpdater
        );
    }
}

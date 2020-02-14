import {Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {BidModifiersEndpoint} from './bid-modifiers.endpoint';
import {BidModifier} from '../types/bid-modifier';
import {BidModifierUploadSummary} from '../types/bid-modifier-upload-summary';
import {RequestStateUpdater} from 'one/app/shared/types/request-state-updater';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import {BidModifierUpdateAction, Breakdown} from '../../../app.constants';
import {tap} from 'rxjs/operators';
import {BidModifierUpdatesService} from './bid-modifier-updates.service';

@Injectable()
export class BidModifiersService {
    constructor(
        private endpoint: BidModifiersEndpoint,
        private bidModifierUpdatesService: BidModifierUpdatesService
    ) {}

    save(
        adGroupId: number,
        bidModifier: BidModifier,
        requestStateUpdater: RequestStateUpdater
    ): Observable<BidModifier> {
        if (!commonHelpers.isDefined(bidModifier.id)) {
            return this.create(adGroupId, bidModifier, requestStateUpdater);
        }
        return this.edit(adGroupId, bidModifier, requestStateUpdater);
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

    private edit(
        adGroupId: number,
        bidModifier: BidModifier,
        requestStateUpdater: RequestStateUpdater
    ): Observable<BidModifier> {
        return this.endpoint
            .edit(adGroupId, bidModifier, requestStateUpdater)
            .pipe(
                tap(bidModifier => {
                    this.bidModifierUpdatesService.registerBidModifierUpdate({
                        adGroupId: adGroupId,
                        bidModifier: bidModifier,
                        action: BidModifierUpdateAction.EDIT,
                    });
                })
            );
    }

    private create(
        adGroupId: number,
        bidModifier: BidModifier,
        requestStateUpdater: RequestStateUpdater
    ): Observable<BidModifier> {
        return this.endpoint
            .create(adGroupId, bidModifier, requestStateUpdater)
            .pipe(
                tap(bidModifier => {
                    this.bidModifierUpdatesService.registerBidModifierUpdate({
                        adGroupId: adGroupId,
                        bidModifier: bidModifier,
                        action: BidModifierUpdateAction.CREATE,
                    });
                })
            );
    }
}

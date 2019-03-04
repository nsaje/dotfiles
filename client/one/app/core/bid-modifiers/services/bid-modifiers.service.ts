import {Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {BidModifiersEndpoint} from './bid-modifiers.endpoint';
import {BidModifier} from '../types/bid-modifier';
import {RequestStateUpdater} from 'one/app/shared/types/request-state-updater';
import * as commonHelpers from '../../../shared/helpers/common.helpers';

@Injectable()
export class BidModifiersService {
    constructor(private endpoint: BidModifiersEndpoint) {}

    saveModifier(
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
}

import {Injectable} from '@angular/core';
import {CampaignEndpoint} from './campaign.endpoint';
import {EntitiesUpdatesService} from '../entities-updates.service';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import {CampaignWithExtras} from '../../types/campaign/campaign-with-extras';
import {Observable} from 'rxjs';
import {Campaign} from '../../types/campaign/campaign';
import {tap} from 'rxjs/operators';
import {EntityType, EntityUpdateAction} from '../../../../app.constants';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {CampaignCloneSettings} from '../../types/campaign/campaign-clone-settings';

@Injectable()
export class CampaignService {
    constructor(
        private endpoint: CampaignEndpoint,
        private entitiesUpdatesService: EntitiesUpdatesService
    ) {}

    defaults(
        accountId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CampaignWithExtras> {
        return this.endpoint.defaults(accountId, requestStateUpdater);
    }

    get(
        id: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CampaignWithExtras> {
        return this.endpoint.get(id, requestStateUpdater);
    }

    list(
        agencyId: string | null,
        accountId: string | null,
        offset: number,
        limit: number,
        keyword: string | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Campaign[]> {
        return this.endpoint.list(
            agencyId,
            accountId,
            offset,
            limit,
            keyword,
            requestStateUpdater
        );
    }

    validate(
        campaign: Partial<Campaign>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        return this.endpoint.validate(campaign, requestStateUpdater);
    }

    save(
        campaign: Campaign,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Campaign> {
        if (!commonHelpers.isDefined(campaign.id)) {
            return this.create(campaign, requestStateUpdater);
        }
        return this.edit(campaign, requestStateUpdater);
    }

    archive(
        id: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Campaign> {
        return this.endpoint
            .edit({id: id, archived: true}, requestStateUpdater)
            .pipe(
                tap(campaign => {
                    this.entitiesUpdatesService.registerEntityUpdate({
                        id: campaign.id,
                        type: EntityType.CAMPAIGN,
                        action: EntityUpdateAction.ARCHIVE,
                    });
                })
            );
    }

    clone(
        campaignId: string,
        requestData: CampaignCloneSettings,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Campaign> {
        return this.endpoint.clone(
            campaignId,
            requestData,
            requestStateUpdater
        );
    }

    private create(
        campaign: Campaign,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Campaign> {
        return this.endpoint.create(campaign, requestStateUpdater).pipe(
            tap(campaign => {
                this.entitiesUpdatesService.registerEntityUpdate({
                    id: campaign.id,
                    type: EntityType.CAMPAIGN,
                    action: EntityUpdateAction.CREATE,
                });
            })
        );
    }

    private edit(
        campaign: Campaign,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Campaign> {
        return this.endpoint.edit(campaign, requestStateUpdater).pipe(
            tap(campaign => {
                this.entitiesUpdatesService.registerEntityUpdate({
                    id: campaign.id,
                    type: EntityType.CAMPAIGN,
                    action: EntityUpdateAction.EDIT,
                });
            })
        );
    }
}

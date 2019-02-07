import {Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {AdGroupEndpoint} from './ad-group.endpoint';
import {tap} from 'rxjs/operators';
import {EntitiesUpdatesService} from './entities-updates.service';
import {EntityType, EntityUpdateAction} from '../../../app.constants';
import {AdGroupWithExtras} from '../types/ad-group/ad-group-with-extras';
import {AdGroup} from '../types/ad-group/ad-group';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';

@Injectable()
export class AdGroupService {
    constructor(
        private endpoint: AdGroupEndpoint,
        private entitiesUpdatesService: EntitiesUpdatesService
    ) {}

    defaults(
        campaignId: number,
        requestStateUpdater: RequestStateUpdater
    ): Observable<AdGroupWithExtras> {
        return this.endpoint.defaults(campaignId, requestStateUpdater);
    }

    get(
        id: number,
        requestStateUpdater: RequestStateUpdater
    ): Observable<AdGroupWithExtras> {
        return this.endpoint.get(id, requestStateUpdater);
    }

    validate(
        adGroup: AdGroup,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        return this.endpoint.validate(adGroup, requestStateUpdater);
    }

    save(
        adGroup: AdGroup,
        requestStateUpdater: RequestStateUpdater
    ): Observable<AdGroup> {
        if (adGroup.id === null) {
            return this.create(adGroup, requestStateUpdater);
        }
        return this.edit(adGroup, requestStateUpdater);
    }

    archive(
        id: number,
        requestStateUpdater: RequestStateUpdater
    ): Observable<AdGroup> {
        return this.endpoint
            .edit({id: id, archived: true}, requestStateUpdater)
            .pipe(
                tap(adGroup => {
                    this.entitiesUpdatesService.registerEntityUpdate({
                        id: adGroup.id,
                        type: EntityType.AD_GROUP,
                        action: EntityUpdateAction.ARCHIVE,
                    });
                })
            );
    }

    private create(
        adGroup: AdGroup,
        requestStateUpdater: RequestStateUpdater
    ): Observable<AdGroup> {
        return this.endpoint.create(adGroup, requestStateUpdater).pipe(
            tap(adGroup => {
                this.entitiesUpdatesService.registerEntityUpdate({
                    id: adGroup.id,
                    type: EntityType.AD_GROUP,
                    action: EntityUpdateAction.CREATE,
                });
            })
        );
    }

    private edit(
        adGroup: AdGroup,
        requestStateUpdater: RequestStateUpdater
    ): Observable<AdGroup> {
        return this.endpoint.edit(adGroup, requestStateUpdater).pipe(
            tap(adGroup => {
                this.entitiesUpdatesService.registerEntityUpdate({
                    id: adGroup.id,
                    type: EntityType.AD_GROUP,
                    action: EntityUpdateAction.EDIT,
                });
            })
        );
    }
}
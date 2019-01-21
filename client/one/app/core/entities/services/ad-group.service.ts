import {Injectable} from '@angular/core';
import {AdGroup} from '../types/ad-group';
import {Observable} from 'rxjs';
import {AdGroupEndpoint} from './ad-group.endpoint';
import {tap} from 'rxjs/operators';
import {EntitiesUpdatesService} from './entities-updates.service';
import {EntityType, EntityUpdateAction} from '../../../app.constants';

@Injectable()
export class AdGroupService {
    constructor(
        private endpoint: AdGroupEndpoint,
        private entitiesUpdatesService: EntitiesUpdatesService
    ) {}

    get(id: number): Observable<AdGroup> {
        return this.endpoint.query(id);
    }

    save(adGroup: AdGroup): Observable<AdGroup> {
        if (adGroup.id === null) {
            return this.create(adGroup);
        }
        return this.edit(adGroup);
    }

    archive(id: number): Observable<AdGroup> {
        return this.endpoint.edit({id: id, archived: true}).pipe(
            tap(adGroup => {
                this.entitiesUpdatesService.registerEntityUpdate({
                    id: adGroup.id,
                    type: EntityType.AD_GROUP,
                    action: EntityUpdateAction.ARCHIVE,
                });
            })
        );
    }

    private create(adGroup: AdGroup): Observable<AdGroup> {
        return this.endpoint.create(adGroup).pipe(
            tap(adGroup => {
                this.entitiesUpdatesService.registerEntityUpdate({
                    id: adGroup.id,
                    type: EntityType.AD_GROUP,
                    action: EntityUpdateAction.CREATE,
                });
            })
        );
    }

    private edit(adGroup: AdGroup): Observable<AdGroup> {
        return this.endpoint.edit(adGroup).pipe(
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

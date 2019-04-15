import {Injectable} from '@angular/core';
import {EntityUpdate} from '../types/entity-update';
import {Observable, Subject} from 'rxjs';
import {downgradeInjectable} from '@angular/upgrade/static';
import {filter} from 'rxjs/operators';
import {EntityType} from '../../../app.constants';

@Injectable()
export class EntitiesUpdatesService {
    private updates$: Observable<EntityUpdate>;
    private _updates$: Subject<EntityUpdate>;

    constructor() {
        this._updates$ = new Subject();
        this.updates$ = this._updates$.asObservable();
    }

    getAllUpdates$(): Observable<EntityUpdate> {
        return this.updates$;
    }

    getUpdatesOfEntity$(
        id: string,
        type: EntityType
    ): Observable<EntityUpdate> {
        return this.updates$.pipe(
            filter(entityUpdate => {
                return (
                    entityUpdate.id === id.toString() &&
                    entityUpdate.type === type
                );
            })
        );
    }

    registerEntityUpdate(entityUpdate: EntityUpdate) {
        this._updates$.next(entityUpdate);
    }
}

declare var angular: angular.IAngularStatic;
angular
    .module('one.downgraded')
    .factory(
        'zemEntitiesUpdatesService',
        downgradeInjectable(EntitiesUpdatesService)
    );

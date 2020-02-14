import {Injectable} from '@angular/core';
import {BidModifierUpdate} from '../types/bid-modifier-update';
import {Observable, Subject} from 'rxjs';
import {downgradeInjectable} from '@angular/upgrade/static';

@Injectable()
export class BidModifierUpdatesService {
    private updates$: Observable<BidModifierUpdate>;
    private _updates$: Subject<BidModifierUpdate>;

    constructor() {
        this._updates$ = new Subject();
        this.updates$ = this._updates$.asObservable();
    }

    getAllUpdates$(): Observable<BidModifierUpdate> {
        return this.updates$;
    }

    registerBidModifierUpdate(bidModifierUpdate: BidModifierUpdate) {
        this._updates$.next(bidModifierUpdate);
    }
}

declare var angular: angular.IAngularStatic;
angular
    .module('one.downgraded')
    .factory(
        'zemBidModifierUpdatesService',
        downgradeInjectable(BidModifierUpdatesService)
    );

import {Injectable, OnDestroy} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {Subject} from 'rxjs';
import {CampaignSettingsStoreState} from './campaign-settings.store.state';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import * as storeHelpers from '../../../../shared/helpers/store.helpers';
import {Campaign} from '../../../../core/entities/types/campaign/campaign';

@Injectable()
export class CampaignSettingsStore extends Store<CampaignSettingsStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;

    constructor() {
        super(new CampaignSettingsStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
    }

    loadEntityDefaults(accountId: string) {
        this.setState({
            ...this.state,
            entity: {id: '12345', goals: []},
        });
    }

    loadEntity(id: string) {
        this.setState({
            ...this.state,
            entity: {id: id, goals: []},
        });
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}

import {Injectable, Injector} from '@angular/core';
import {Store} from '../../../../../shared/services/store/store';
import {RequestStateUpdater} from '../../../../../shared/types/request-state-updater';
import {CreativeTagsStoreState} from './creative-tags-store.state';
import {getStoreRequestStateUpdater} from '../../../../../shared/helpers/store.helpers';
import {StoreProvider} from '../../../../../shared/services/store/store.provider';
import {StoreAction} from '../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../shared/services/store/store.reducer';
import {StoreEffect} from '../../../../../shared/services/store/store.effect';
import {
    SetAvailableTagsAction,
    SetAvailableTagsActionReducer,
} from './reducers/set-available-tags.reducer';
import {
    FetchCreativeTagsAction,
    FetchCreativeTagsActionEffect,
} from './effects/fetch-creative-tags.effect';
import {ScopeParams} from '../../../../../shared/types/scope-params';

@Injectable()
export class CreativeTagsStore extends Store<CreativeTagsStoreState> {
    private requestStateUpdater: RequestStateUpdater;

    constructor(injector: Injector) {
        super(new CreativeTagsStoreState(), injector);
        this.requestStateUpdater = getStoreRequestStateUpdater(this);
    }

    provide(): StoreProvider<
        StoreAction<any>,
        | StoreReducer<CreativeTagsStoreState, StoreAction<any>>
        | StoreEffect<CreativeTagsStoreState, StoreAction<any>>
    >[] {
        return [
            {
                provide: SetAvailableTagsAction,
                useClass: SetAvailableTagsActionReducer,
            },
            {
                provide: FetchCreativeTagsAction,
                useClass: FetchCreativeTagsActionEffect,
            },
        ];
    }

    setStore(scope: ScopeParams) {
        this.loadTags(scope, null, true);
    }

    loadTags(
        scope: ScopeParams,
        keyword: string = null,
        forceReload: boolean = false
    ) {
        this.dispatch(
            new FetchCreativeTagsAction({
                scope,
                searchParams: {keyword},
                forceReload,
                requestStateUpdater: this.requestStateUpdater,
            })
        );
    }
}

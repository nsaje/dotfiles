import {Injectable, Injector} from '@angular/core';
import {Store} from '../../../../../shared/services/store/store';
import {CreativesStoreState} from './creatives.store.state';
import {RequestStateUpdater} from '../../../../../shared/types/request-state-updater';
import {getStoreRequestStateUpdater} from '../../../../../shared/helpers/store.helpers';
import {CreativesService} from '../../../../../core/creatives/services/creatives.service';
import {StoreProvider} from '../../../../../shared/services/store/store.provider';
import {StoreAction} from '../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../shared/services/store/store.reducer';
import {StoreEffect} from '../../../../../shared/services/store/store.effect';
import {
    SetCreativesAction,
    SetCreativesActionReducer,
} from './reducers/set-creatives.reducer';
import {
    FetchCreativesAction,
    FetchCreativesActionEffect,
} from './effects/fetch-creatives.effect';
import {
    SetScopeAction,
    SetScopeActionReducer,
} from './reducers/set-scope.reducer';
import {ScopeParams} from '../../../../../shared/types/scope-params';
import {CreativesSearchParams} from '../../types/creatives-search-params';
import {PaginationState} from '../../../../../shared/components/smart-grid/types/pagination-state';

@Injectable()
export class CreativesStore extends Store<CreativesStoreState> {
    private requestStateUpdater: RequestStateUpdater;

    constructor(
        private creativesService: CreativesService,
        injector: Injector
    ) {
        super(new CreativesStoreState(), injector);
        this.requestStateUpdater = getStoreRequestStateUpdater(this);
    }

    provide(): StoreProvider<
        StoreAction<any>,
        | StoreReducer<CreativesStoreState, StoreAction<any>>
        | StoreEffect<CreativesStoreState, StoreAction<any>>
    >[] {
        return [
            {
                provide: SetCreativesAction,
                useClass: SetCreativesActionReducer,
            },
            {
                provide: SetScopeAction,
                useClass: SetScopeActionReducer,
            },
            {
                provide: FetchCreativesAction,
                useClass: FetchCreativesActionEffect,
            },
        ];
    }

    setStore(
        scope: ScopeParams,
        pagination: PaginationState,
        searchParams: CreativesSearchParams
    ): Promise<boolean> {
        return this.loadCreatives(scope, pagination, searchParams);
    }

    loadEntities(
        pagination: PaginationState,
        searchParams: CreativesSearchParams
    ): Promise<boolean> {
        return this.loadCreatives(this.state.scope, pagination, searchParams);
    }

    private loadCreatives(
        scope: ScopeParams,
        pagination: PaginationState,
        searchParams: CreativesSearchParams
    ): Promise<boolean> {
        return this.dispatch(
            new FetchCreativesAction({
                scope,
                pagination,
                searchParams,
                requestStateUpdater: this.requestStateUpdater,
            })
        );
    }
}

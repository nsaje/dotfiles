import {Injectable, Injector} from '@angular/core';
import {Store} from '../../../../../shared/services/store/store';
import {CreativeBatchStoreState} from './creative-batch.store.state';
import {RequestStateUpdater} from '../../../../../shared/types/request-state-updater';
import {StoreProvider} from '../../../../../shared/services/store/store.provider';
import {StoreAction} from '../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../shared/services/store/store.reducer';
import {StoreEffect} from '../../../../../shared/services/store/store.effect';
import {CreativesService} from '../../../../../core/creatives/services/creatives.service';
import {getStoreRequestStateUpdater} from '../../../../../shared/helpers/store.helpers';
import {
    SetEntityAction,
    SetEntityActionReducer,
} from './reducers/set-entity.reducer';
import {
    FetchCreativeBatchAction,
    FetchCreativeBatchActionEffect,
} from './effects/fetch-creative-batch.effect';
import {ScopeParams} from '../../../../../shared/types/scope-params';
import {
    CreateCreativeBatchAction,
    CreateCreativeBatchActionEffect,
} from './effects/create-creative-batch.effect';
import {
    ValidateCreativeBatchAction,
    ValidateCreativeBatchActionEffect,
} from './effects/validate-creative-batch.effect';
import {
    SetFieldsErrorsAction,
    SetFieldsErrorsActionReducer,
} from './reducers/set-fields-errors.reducer';
import {
    EditCreativeBatchAction,
    EditCreativeBatchActionEffect,
} from './effects/edit-creative-batch.effect';

@Injectable()
export class CreativeBatchStore extends Store<CreativeBatchStoreState> {
    private requestStateUpdater: RequestStateUpdater;

    constructor(
        private creativesService: CreativesService,
        injector: Injector
    ) {
        super(new CreativeBatchStoreState(), injector);
        this.requestStateUpdater = getStoreRequestStateUpdater(this);
    }

    provide(): StoreProvider<
        StoreAction<any>,
        | StoreReducer<CreativeBatchStoreState, StoreAction<any>>
        | StoreEffect<CreativeBatchStoreState, StoreAction<any>>
    >[] {
        return [
            {
                provide: FetchCreativeBatchAction,
                useClass: FetchCreativeBatchActionEffect,
            },
            {
                provide: CreateCreativeBatchAction,
                useClass: CreateCreativeBatchActionEffect,
            },
            {
                provide: EditCreativeBatchAction,
                useClass: EditCreativeBatchActionEffect,
            },
            {
                provide: ValidateCreativeBatchAction,
                useClass: ValidateCreativeBatchActionEffect,
            },
            {
                provide: SetEntityAction,
                useClass: SetEntityActionReducer,
            },
            {
                provide: SetFieldsErrorsAction,
                useClass: SetFieldsErrorsActionReducer,
            },
        ];
    }

    loadEntity(batchId: string) {
        this.dispatch(
            new FetchCreativeBatchAction({
                batchId,
                requestStateUpdater: this.requestStateUpdater,
            })
        );
    }

    createEntity(scope: ScopeParams) {
        this.dispatch(
            new CreateCreativeBatchAction({
                scope,
                requestStateUpdater: this.requestStateUpdater,
            })
        );
    }

    validateEntity() {
        this.dispatch(
            new ValidateCreativeBatchAction({
                requestStateUpdater: this.requestStateUpdater,
            })
        );
    }

    saveEntity() {
        this.dispatch(
            new EditCreativeBatchAction({
                requestStateUpdater: this.requestStateUpdater,
            })
        );
    }
}

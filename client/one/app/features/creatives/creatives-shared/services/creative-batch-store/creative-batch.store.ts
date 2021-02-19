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
import {CreativeBatch} from '../../../../../core/creatives/types/creative-batch';
import {
    CreativeBatchMode,
    CreativeBatchType,
} from '../../../../../app.constants';
import {
    CreateCreativeCandidateAction,
    CreateCreativeCandidateActionEffect,
} from './effects/create-creative-candidate.effect';
import {
    EditCreativeCandidateAction,
    EditCreativeCandidateActionEffect,
} from './effects/edit-creative-candidate.effect';
import {
    SetCandidatesAction,
    SetCandidatesActionReducer,
} from './reducers/set-candidates.reducer';
import {
    FetchCreativeCandidatesAction,
    FetchCreativeCandidatesActionEffect,
} from './effects/fetch-creative-candidates.effect';
import {CreativeCandidate} from '../../../../../core/creatives/types/creative-candidate';
import {MAX_LOADED_CANDIDATES} from '../../creatives-shared.config';
import {
    SetSelectedCandidateAction,
    SetSelectedCandidateActionReducer,
} from './reducers/set-selected-candidate.reducer';
import {
    RemoveCreativeCandidateAction,
    RemoveCreativeCandidateActionEffect,
} from './effects/remove-creative-candidate.effect';

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
                provide: SetEntityAction,
                useClass: SetEntityActionReducer,
            },
            {
                provide: SetFieldsErrorsAction,
                useClass: SetFieldsErrorsActionReducer,
            },
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
                provide: FetchCreativeCandidatesAction,
                useClass: FetchCreativeCandidatesActionEffect,
            },
            {
                provide: CreateCreativeCandidateAction,
                useClass: CreateCreativeCandidateActionEffect,
            },
            {
                provide: EditCreativeCandidateAction,
                useClass: EditCreativeCandidateActionEffect,
            },
            {
                provide: SetCandidatesAction,
                useClass: SetCandidatesActionReducer,
            },
            {
                provide: SetSelectedCandidateAction,
                useClass: SetSelectedCandidateActionReducer,
            },
            {
                provide: RemoveCreativeCandidateAction,
                useClass: RemoveCreativeCandidateActionEffect,
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
        this.dispatch(
            new FetchCreativeCandidatesAction({
                batchId,
                pagination: {page: 1, pageSize: MAX_LOADED_CANDIDATES}, // TODO: What if there are more candidates than this?
                requestStateUpdater: this.requestStateUpdater,
            })
        );
    }

    createEntity(
        scope: ScopeParams,
        type: CreativeBatchType,
        mode: CreativeBatchMode
    ) {
        this.dispatch(
            new CreateCreativeBatchAction({
                scope,
                type,
                mode,
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

    addCandidate() {
        this.dispatch(
            new CreateCreativeCandidateAction({
                requestStateUpdater: this.requestStateUpdater,
            })
        );
    }

    updateCandidate(candidate: CreativeCandidate) {
        this.dispatch(
            new EditCreativeCandidateAction({
                candidate,
                requestStateUpdater: this.requestStateUpdater,
            })
        );
    }

    selectCandidate(candidate: CreativeCandidate) {
        this.dispatch(new SetSelectedCandidateAction(candidate));
    }

    deleteCandidate(candidate: CreativeCandidate) {
        this.dispatch(
            new RemoveCreativeCandidateAction({
                candidate,
                requestStateUpdater: this.requestStateUpdater,
            })
        );
    }

    updateBatchName(name: string) {
        this.updateBatch({name});
    }

    updateTags(tags: string[]) {
        this.updateBatch({tags});
    }

    private updateBatch(updates: Partial<CreativeBatch>) {
        this.dispatch(
            new SetEntityAction({...this.state.entity, ...updates})
        ).then(x => this.saveEntity());
    }
}

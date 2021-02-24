import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {Injectable} from '@angular/core';
import {StoreEffect} from '../../../../../../shared/services/store/store.effect';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {CreativesService} from '../../../../../../core/creatives/services/creatives.service';
import {CreativeCandidate} from '../../../../../../core/creatives/types/creative-candidate';
import {takeUntil} from 'rxjs/operators';
import {SetCandidatesAction} from '../reducers/set-candidates.reducer';
import {replaceArrayItem} from '../../../../../../shared/helpers/array.helpers';

export interface EditCreativeCandidateParams {
    candidate: CreativeCandidate;
    changes: Partial<CreativeCandidate>;
    requestStateUpdater: RequestStateUpdater;
}

export class EditCreativeCandidateAction extends StoreAction<
    EditCreativeCandidateParams
> {}

// tslint:disable-next-line: max-classes-per-file
@Injectable()
export class EditCreativeCandidateActionEffect extends StoreEffect<
    CreativeBatchStoreState,
    EditCreativeCandidateAction
> {
    constructor(private service: CreativesService) {
        super();
    }

    effect(
        state: CreativeBatchStoreState,
        action: EditCreativeCandidateAction
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            const params: EditCreativeCandidateParams = action.payload;
            this.service
                .editCandidate(
                    state.entity.id,
                    params.candidate.id,
                    {
                        type: params.candidate.type,
                        ...params.changes,
                    },
                    params.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (candidate: CreativeCandidate) => {
                        this.dispatch(
                            new SetCandidatesAction(
                                replaceArrayItem(
                                    state.candidates,
                                    candidate => candidate.id,
                                    candidate
                                )
                            )
                        );
                        resolve(true);
                    },
                    () => {
                        resolve(false);
                    }
                );
        });
    }
}

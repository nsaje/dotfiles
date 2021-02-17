import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {Injectable} from '@angular/core';
import {StoreEffect} from '../../../../../../shared/services/store/store.effect';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {CreativesService} from '../../../../../../core/creatives/services/creatives.service';
import {takeUntil} from 'rxjs/operators';
import {CreativeCandidate} from '../../../../../../core/creatives/types/creative-candidate';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {SetCandidatesAction} from '../reducers/set-candidates.reducer';

export interface CreateCreativeCandidateParams {
    requestStateUpdater: RequestStateUpdater;
}

export class CreateCreativeCandidateAction extends StoreAction<
    CreateCreativeCandidateParams
> {}

// tslint:disable-next-line: max-classes-per-file
@Injectable()
export class CreateCreativeCandidateActionEffect extends StoreEffect<
    CreativeBatchStoreState,
    CreateCreativeCandidateAction
> {
    constructor(private service: CreativesService) {
        super();
    }

    effect(
        state: CreativeBatchStoreState,
        action: CreateCreativeCandidateAction
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            const params: CreateCreativeCandidateParams = action.payload;
            const newCandidate: CreativeCandidate = {};
            this.service
                .createCandidate(
                    state.entity.id,
                    newCandidate,
                    params.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (candidate: CreativeCandidate) => {
                        this.dispatch(
                            new SetCandidatesAction([
                                ...state.candidates,
                                candidate,
                            ])
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

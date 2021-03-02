import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../../shared/services/store/store.reducer';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {CreativeCandidate} from '../../../../../../core/creatives/types/creative-candidate';
import {isDefined} from '../../../../../../shared/helpers/common.helpers';
import {AdSizeConfig} from '../../../types/ad-size-config';
import {AD_SIZES} from '../../../creatives-shared.config';

export class SetCandidatesAction extends StoreAction<CreativeCandidate[]> {}

// tslint:disable-next-line: max-classes-per-file
export class SetCandidatesActionReducer extends StoreReducer<
    CreativeBatchStoreState,
    SetCandidatesAction
> {
    reduce(
        state: CreativeBatchStoreState,
        action: SetCandidatesAction
    ): CreativeBatchStoreState {
        return {
            ...state,
            candidates: action.payload.map(this.mapCandidateToFrontend),
        };
    }

    private mapCandidateToFrontend(
        candidate: CreativeCandidate
    ): CreativeCandidate {
        const result: CreativeCandidate = {...candidate};
        if (
            isDefined(candidate.imageWidth) &&
            isDefined(candidate.imageHeight)
        ) {
            const dimensions: AdSizeConfig = AD_SIZES.find(
                x =>
                    x.width === candidate.imageWidth &&
                    x.height === candidate.imageHeight
            );
            delete result.imageWidth;
            delete result.imageHeight;
            result.size = dimensions.size;
        }
        return result;
    }
}

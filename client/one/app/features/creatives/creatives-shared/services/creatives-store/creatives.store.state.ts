import {Creative} from '../../../../../core/creatives/types/creative';
import {RequestState} from '../../../../../shared/types/request-state';
import {CreativesStoreFieldsErrorsState} from './creatives.store.fields-errors-state';
import {ScopeSelectorState} from '../../../../../shared/components/scope-selector/scope-selector.constants';
import {ScopeParams} from '../../../../../shared/types/scope-params';

export class CreativesStoreState {
    scope: ScopeParams = null;
    hasAgencyScope: boolean = null;
    entities: Creative[] = [];
    fieldsErrors: CreativesStoreFieldsErrorsState[] = [];
    availableTags: string[] = [];
    activeEntity = {
        entity: {
            id: null,
            agencyId: null,
            agencyName: null,
            accountId: null,
            accountName: null,
            type: null,
            url: null,
            title: null,
            displayUrl: null,
            brandName: null,
            description: null,
            callToAction: null,
            tags: null,
            imageUrl: null,
            iconUrl: null,
            adTag: null,
            videoAssetId: null,
            trackers: null,
        } as Creative,
        scopeState: null as ScopeSelectorState,
        isReadOnly: null as boolean,
        fieldsErrors: new CreativesStoreFieldsErrorsState(),
    };
    selectedEntityIds: string[] = [];
    requests = {
        list: {} as RequestState,
    };
}

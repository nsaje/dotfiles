import {RequestState} from '../../../../shared/types/request-state';

export interface AdGroupRequests {
    defaults: RequestState;
    get: RequestState;
    validate: RequestState;
    create: RequestState;
    edit: RequestState;
}

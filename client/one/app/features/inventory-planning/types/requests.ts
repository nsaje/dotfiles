import {RequestState} from '../../../shared/types/request-state';

export interface Requests {
    summary: RequestState;
    countries: RequestState;
    publishers: RequestState;
    devices: RequestState;
    sources: RequestState;
}

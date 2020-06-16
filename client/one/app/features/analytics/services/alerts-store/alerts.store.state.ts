import {Alert} from '../../../../core/alerts/types/alert';
import {RequestState} from '../../../../shared/types/request-state';

export class AlertsStoreState {
    alerts: Alert[] = [];
    requests = {
        listAccounts: {} as RequestState,
        listAccount: {} as RequestState,
        listCampaign: {} as RequestState,
        listAdGroup: {} as RequestState,
    };
}

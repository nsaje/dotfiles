import {CreditTotal} from '../../../../core/credits/types/credit-total';
import {Credit} from '../../../../core/credits/types/credit';
import {CampaignBudget} from '../../../../core/entities/types/campaign/campaign-budget';
import {Account} from '../../../../core/entities/types/account/account';
import {ScopeSelectorState} from '../../../../shared/components/scope-selector/scope-selector.constants';
import {CreditRefund} from '../../../../core/credits/types/credit-refund';
import {RequestState} from '../../../../shared/types/request-state';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {CreditsStoreFieldsErrorsState} from './credits.store.fields-errors-state';

export class CreditsStoreState {
    agencyId: string = null;
    accountId: string = null;
    hasAgencyScope: boolean = false;

    totals: CreditTotal[] = [];
    activeCredits: Credit[] = [];
    pastCredits: Credit[] = [];
    creditRefunds: CreditRefund[] = [];
    accounts: Account[] = [];

    creditActiveEntity = {
        entity: {
            id: null,
            agencyId: null,
            accountId: null,
            startDate: null,
            endDate: null,
            licenseFee: null,
            serviceFee: null,
            status: null,
            currency: null,
            amount: null,
            contractId: null,
            contractNumber: null,
            comment: null,
        } as Credit,
        scopeState: null as ScopeSelectorState,
        isReadOnly: false as boolean,
        isSigned: false as boolean,
        campaignBudgets: [] as CampaignBudget[],
        fieldsErrors: new CreditsStoreFieldsErrorsState(),
    };

    creditRefundActiveEntity = {
        entity: {
            id: null,
            accountId: null,
            startDate: null,
            amount: null,
            effectiveMargin: null,
            comment: null,
        } as CreditRefund,
        fieldsErrors: new CreditsStoreFieldsErrorsState(),
    };

    requests = {
        listActive: {} as RequestState,
        listPast: {} as RequestState,
        create: {} as RequestState,
        edit: {} as RequestState,
        totals: {} as RequestState,
        listBudgets: {} as RequestState,
        listRefunds: {} as RequestState,
        createRefund: {} as RequestState,
    };
    accountsRequests = {
        list: {} as RequestState,
    };

    activePaginationOptions: PaginationOptions;
    pastPaginationOptions: PaginationOptions;
    excludeCanceled: boolean = true;
}

import './credits.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnInit,
    HostBinding,
    OnDestroy,
    ViewChild,
} from '@angular/core';
import {ActivatedRoute, ParamMap, Router} from '@angular/router';
import {Subject} from 'rxjs';
import {takeUntil, filter} from 'rxjs/operators';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {CreditsStore} from '../../services/credits-store/credits.store';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {PaginationState} from '../../../../shared/components/smart-grid/types/pagination-state';
import {ModalComponent} from '../../../../shared/components/modal/modal.component';
import {Credit} from '../../../../core/credits/types/credit';
import {
    DEFAULT_PAGINATION,
    ACTIVE_PAGINATION_URL_PARAMS,
    PAST_PAGINATION_URL_PARAMS,
    DEFAULT_PAGINATION_OPTIONS,
} from '../../credits.config';
import {CreditStatus} from '../../../../app.constants';
import {CreditGridType} from '../../credits.constants';
import {AuthStore} from '../../../../core/auth/services/auth.store';
import {EntityPermissionValue} from '../../../../core/users/users.constants';
import {isDefined} from '../../../../shared/helpers/common.helpers';

@Component({
    selector: 'zem-credits-view',
    templateUrl: './credits.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [CreditsStore],
})
export class CreditsView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-credits-view';
    @ViewChild('creditItemModal', {static: false})
    creditItemModal: ModalComponent;
    @ViewChild('creditRefundCreateModal', {static: false})
    creditRefundCreateModal: ModalComponent;
    @ViewChild('creditRefundListModal', {static: false})
    creditRefundListModal: ModalComponent;

    context: any;

    agencyId: string;
    accountId: string;

    activePaginationOptions: PaginationOptions = DEFAULT_PAGINATION_OPTIONS;
    pastPaginationOptions: PaginationOptions = DEFAULT_PAGINATION_OPTIONS;
    refundPaginationOptions: PaginationOptions = DEFAULT_PAGINATION_OPTIONS;

    creditRefundCreateModalTitle: string;
    creditRefundListModalTitle: string;
    creditItemModalTitle: string;

    creditGridType = CreditGridType;

    showLicenseFee: boolean = false;
    showServiceFee: boolean = false;

    isReadOnly: boolean = true;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: CreditsStore,
        public authStore: AuthStore,
        private route: ActivatedRoute,
        private router: Router
    ) {
        this.context = {
            componentParent: this,
        };

        this.showLicenseFee = this.authStore.hasPermissionOnAnyEntity(
            EntityPermissionValue.MEDIA_COST_DATA_COST_LICENCE_FEE
        );
        this.showServiceFee = this.authStore.hasPermissionOnAnyEntity(
            EntityPermissionValue.BASE_COSTS_SERVICE_FEE
        );
    }

    ngOnInit(): void {
        this.route.queryParams
            .pipe(takeUntil(this.ngUnsubscribe$))
            .pipe(
                filter(queryParams =>
                    commonHelpers.isDefined(queryParams.agencyId)
                )
            )
            .subscribe(queryParams => {
                this.updateInternalState(queryParams);
            });
    }

    openCreditItemModal(credit: Partial<Credit>): void {
        this.creditItemModalTitle = credit.id
            ? `Edit Credit Item #${credit.id}`
            : 'Add Credit Item';
        this.store.setCreditActiveEntity(credit);
        this.store.loadCreditActiveEntityBudgets();
        this.creditItemModal.open();
    }

    openCreditRefundCreateModal(credit: Credit): void {
        this.creditRefundCreateModalTitle = `Credit Item #${credit.id} refund`;
        this.store.setCreditActiveEntity(credit);
        this.store.setCreditRefundActiveEntity({
            amount: 0,
            accountId: credit.accountId,
        });
        this.creditRefundCreateModal.open();
    }

    openCreditRefundListModal(credit: Credit): void {
        this.creditRefundListModalTitle = `Credit Item #${credit.id} refund list`;
        this.refundPaginationOptions = DEFAULT_PAGINATION_OPTIONS;
        this.store.setCreditActiveEntity(credit);
        this.store
            .loadRefunds(credit.id, this.refundPaginationOptions)
            .then(() => {
                this.creditRefundListModal.open();
            });
    }

    addCreditItem(): void {
        this.openCreditItemModal({
            agencyId: this.store.state.accountId
                ? null
                : this.store.state.agencyId,
            accountId: this.store.state.accountId,
            currency: this.store.getDefaultCurrency(),
            status: CreditStatus.PENDING,
        });
    }

    saveCreditItem(): void {
        this.store.saveCreditActiveEntity().then(() => {
            this.creditItemModal.close();
            this.store.loadEntities(true, this.activePaginationOptions);
        });
    }

    cancelCreditItem(credit: Credit): void {
        if (
            confirm(
                `Are you sure you want to cancel the credit line item #${credit.id}?`
            )
        ) {
            this.store.setCreditActiveEntity(credit);
            this.store.cancelCreditActiveEntity().then(() => {
                this.store.loadEntities(true, this.activePaginationOptions);
            });
        }
    }

    saveCreditRefund(): void {
        this.store.saveCreditRefundActiveEntity().then(() => {
            this.creditRefundCreateModal.close();
            this.store.loadEntities(true, this.activePaginationOptions);
        });
    }

    onCreditPaginationChange($event: PaginationState) {
        this.router.navigate([], {
            relativeTo: this.route,
            queryParams: $event,
            queryParamsHandling: 'merge',
            replaceUrl: true,
        });
    }

    onRefundPaginationChange($event: PaginationState) {
        this.refundPaginationOptions = {
            ...this.refundPaginationOptions,
            ...$event,
        };
        this.store.loadRefunds(
            this.store.state.creditActiveEntity.entity.id,
            this.refundPaginationOptions
        );
    }

    onExcludeCanceledChange($event: boolean) {
        this.router.navigate([], {
            relativeTo: this.route,
            queryParams: {
                excludeCanceled: $event,
            },
            queryParamsHandling: 'merge',
            replaceUrl: true,
        });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    private updateInternalState(queryParams: any): void {
        const agencyId: string = queryParams.agencyId;
        const accountId: string | null = queryParams.accountId || null;
        const excludeCanceled = isDefined(queryParams.excludeCanceled)
            ? queryParams.excludeCanceled === 'true'
            : this.store.state.excludeCanceled;

        this.activePaginationOptions = {
            ...this.activePaginationOptions,
            ...this.getPreselectedPagination(ACTIVE_PAGINATION_URL_PARAMS),
        };
        this.pastPaginationOptions = {
            ...this.pastPaginationOptions,
            ...this.getPreselectedPagination(PAST_PAGINATION_URL_PARAMS),
        };

        this.store.setStore(
            agencyId,
            accountId,
            excludeCanceled,
            this.activePaginationOptions,
            this.pastPaginationOptions
        );

        this.isReadOnly = this.authStore.hasReadOnlyAccessOn(
            agencyId,
            accountId
        );
    }

    private getPreselectedPagination(paginationParams: {
        [key: string]: keyof PaginationState;
    }): PaginationState {
        const pagination: PaginationState = {...DEFAULT_PAGINATION};
        Object.keys(paginationParams).forEach(paramName => {
            const queryParams: ParamMap = this.route.snapshot.queryParamMap;
            const paramValue: string = queryParams.get(paramName);
            if (paramValue) {
                const paramKey: keyof PaginationState =
                    paginationParams[paramName];
                pagination[paramKey] = Number(paramValue);
            }
        });
        return pagination;
    }
}

import './rules.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnInit,
    OnDestroy,
    HostBinding,
    ViewChild,
} from '@angular/core';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {Subject} from 'rxjs';
import {ActivatedRoute, Router} from '@angular/router';
import {takeUntil, filter} from 'rxjs/operators';
import {PaginationState} from '../../../../shared/components/smart-grid/types/pagination-state';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {RulesStore} from '../../services/rules-store/rules.store';
import {
    DEFAULT_PAGINATION_OPTIONS,
    DEFAULT_PAGINATION,
    PAGINATION_URL_PARAMS,
} from '../../rules.config';
import {Rule} from '../../../../core/rules/types/rule';
import {ModalComponent} from '../../../../shared/components/modal/modal.component';
import {RuleEditFormApi} from '../../components/rule-edit-form/types/rule-edit-form-api';

@Component({
    selector: 'zem-rules-view',
    templateUrl: './rules.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [RulesStore],
})
export class RulesView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-rules-view';
    @ViewChild('editRuleModal', {static: false})
    editRuleModal: ModalComponent;

    context: any;

    keyword: string;
    paginationOptions: PaginationOptions = DEFAULT_PAGINATION_OPTIONS;

    isRuleSaveInProgress: boolean = false;

    private ngUnsubscribe$: Subject<void> = new Subject();
    private ruleEditFormApi: RuleEditFormApi;

    constructor(
        public store: RulesStore,
        private route: ActivatedRoute,
        private router: Router
    ) {
        this.context = {
            componentParent: this,
        };
    }

    ngOnInit() {
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

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    onPaginationChange($event: PaginationState) {
        this.router.navigate([], {
            relativeTo: this.route,
            queryParams: $event,
            queryParamsHandling: 'merge',
            replaceUrl: true,
        });
    }

    searchRules(keyword: string) {
        this.router.navigate([], {
            relativeTo: this.route,
            queryParams: {keyword: keyword},
            queryParamsHandling: 'merge',
            replaceUrl: true,
        });
    }

    removeRule(rule: Rule) {
        if (confirm(`Are you sure you wish to delete rule ${rule.name}?`)) {
            this.store.archiveEntity(rule.id).then(() => {
                this.store.loadEntities(
                    this.paginationOptions.page,
                    this.paginationOptions.pageSize,
                    this.keyword
                );
            });
        }
    }

    onRuleStateToggle(rule: Rule, value: boolean): void {
        if (value) {
            this.store.enableRule(rule.id);
        } else {
            this.store.pauseRule(rule.id);
        }
    }

    saveRule(): void {
        this.isRuleSaveInProgress = true;
        this.ruleEditFormApi
            .executeSave()
            .then(() => {
                this.store.loadEntities(
                    this.paginationOptions.page,
                    this.paginationOptions.pageSize,
                    this.keyword
                );
                this.isRuleSaveInProgress = false;
                this.editRuleModal.close();
            })
            .catch(() => {
                this.isRuleSaveInProgress = false;
            });
    }

    onRuleEditFormReady(ruleEditFormApi: RuleEditFormApi) {
        this.ruleEditFormApi = ruleEditFormApi;
    }

    openEditRuleModal(rule: Partial<Rule>) {
        if (commonHelpers.isDefined(rule.id)) {
            this.store.setActiveEntity(rule);
        }
        this.editRuleModal.open();
    }

    closeEditRuleModal() {
        this.store.setActiveEntity({});
        this.editRuleModal.close();
    }

    private updateInternalState(queryParams: any) {
        const agencyId = queryParams.agencyId;
        const accountId = queryParams.accountId || null;
        this.keyword = queryParams.keyword || null;
        this.paginationOptions = {
            ...this.paginationOptions,
            ...this.getPreselectedPagination(),
        };

        if (
            agencyId !== this.store.state.agencyId ||
            accountId !== this.store.state.accountId
        ) {
            this.store.setStore(
                agencyId,
                accountId,
                this.paginationOptions.page,
                this.paginationOptions.pageSize,
                this.keyword
            );
        } else {
            this.store.loadEntities(
                this.paginationOptions.page,
                this.paginationOptions.pageSize,
                this.keyword
            );
        }
    }

    private getPreselectedPagination(): {page: number; pageSize: number} {
        const pagination: PaginationState = {...DEFAULT_PAGINATION};
        PAGINATION_URL_PARAMS.forEach(paramName => {
            const value: string = this.route.snapshot.queryParamMap.get(
                paramName
            );
            if (value) {
                pagination[paramName] = Number(value);
            }
        });
        return pagination;
    }
}

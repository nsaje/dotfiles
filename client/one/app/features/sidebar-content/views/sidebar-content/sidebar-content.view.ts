import './sidebar-content.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    OnInit,
    OnDestroy,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import {SidebarContentStore} from '../../services/sidebar-content.store';
import {ListGroupItem} from '../../../../shared/components/list-group/types/list-group-item';
import {ListGroupItemIcon} from '../../../../shared/components/list-group/components/list-group-item/list-group-item.component.constants';
import * as routerHelpers from '../../../../shared/helpers/router.helpers';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import * as arrayHelpers from '../../../../shared/helpers/array.helpers';
import {Subject, Observable, merge} from 'rxjs';
import {takeUntil, distinctUntilChanged, tap, filter} from 'rxjs/operators';
import {RoutePathName} from '../../../../app.constants';
import {Router} from '@angular/router';
import {AuthStore} from '../../../../core/auth/services/auth.store';

@Component({
    selector: 'zem-sidebar-content-view',
    templateUrl: './sidebar-content.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [SidebarContentStore],
})
export class SidebarContentView implements OnInit, OnChanges, OnDestroy {
    @Input()
    routePathNames: RoutePathName[];
    @Input()
    isOpen: boolean;

    rootPath: RoutePathName[] = [RoutePathName.APP_BASE];

    items: ListGroupItem[] = [
        {
            value: RoutePathName.CREDITS,
            displayValue: 'Credits',
            icon: ListGroupItemIcon.Credit,
            isVisible: () => {
                return this.authStore.hasPermission(
                    'zemauth.account_credit_view'
                );
            },
        },
        {
            value: RoutePathName.DEALS,
            displayValue: 'Deals',
            icon: ListGroupItemIcon.Folder,
            isVisible: () => true,
        },
        {
            value: RoutePathName.USERS,
            displayValue: 'User management',
            icon: ListGroupItemIcon.User,
            isVisible: () => true,
            isNewFeature: true,
        },
        {
            value: RoutePathName.PUBLISHER_GROUPS,
            displayValue: 'Publishers & placements',
            icon: ListGroupItemIcon.PublisherGroups,
            isVisible: () => true,
        },
        {
            value: RoutePathName.RULES,
            displayValue: 'Automation rules',
            icon: ListGroupItemIcon.AutomationRules,
            isVisible: () => {
                return this.authStore.hasPermission(
                    'zemauth.fea_can_create_automation_rules'
                );
            },
            isNewFeature: true,
            subItems: [
                {
                    value: '',
                    displayValue: 'Library',
                    isVisible: () => {
                        return this.authStore.hasPermission(
                            'zemauth.fea_can_create_automation_rules'
                        );
                    },
                },
                {
                    value: RoutePathName.RULES_HISTORY,
                    displayValue: 'History',
                    isVisible: () => {
                        return this.authStore.hasPermission(
                            'zemauth.fea_can_create_automation_rules'
                        );
                    },
                },
            ],
        },
        {
            value: RoutePathName.CREATIVES,
            displayValue: 'Creative library',
            icon: ListGroupItemIcon.Creatives,
            isVisible: () => {
                return this.authStore.hasPermission(
                    'zemauth.can_see_creative_library'
                );
            },
        },
    ];

    hasAgencyScope: boolean;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: SidebarContentStore,
        private authStore: AuthStore,
        private router: Router
    ) {}

    ngOnInit(): void {
        this.subscribeToStoreStateUpdates();
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.routePathNames) {
            const route = routerHelpers.getActivatedRoute(this.router);
            const agencyId = route.snapshot.queryParamMap.get('agencyId');
            const accountId = route.snapshot.queryParamMap.get('accountId');
            if (
                agencyId !== this.store.state.selectedAgencyId ||
                accountId !== this.store.state.selectedAccountId ||
                (accountId === null && agencyId === null)
            ) {
                this.hasAgencyScope = this.authStore.hasAgencyScope(agencyId);
                this.store.setStore(agencyId, accountId);
            }
        }
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    onRoutePathChange($event: RoutePathName[]) {
        if (!arrayHelpers.isEqual(this.routePathNames, $event)) {
            const route = routerHelpers.getActivatedRoute(this.router);
            this.router.navigate($event, {
                queryParams: commonHelpers.getValueWithOnlyProps(
                    route.snapshot.queryParams,
                    ['agencyId', 'accountId']
                ),
            });
        }
    }

    private subscribeToStoreStateUpdates() {
        merge(this.stateUpdater$())
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe();
    }

    private stateUpdater$(): Observable<any> {
        return this.store.state$.pipe(
            filter(
                state =>
                    commonHelpers.isDefined(state.selectedAgencyId) ||
                    commonHelpers.isDefined(state.selectedAccountId)
            ),
            distinctUntilChanged(),
            tap(state => {
                const route = routerHelpers.getActivatedRoute(this.router);
                this.hasAgencyScope = this.authStore.hasAgencyScope(
                    state.selectedAgencyId
                );

                this.router.navigate([], {
                    relativeTo: route,
                    queryParams: {
                        agencyId: state.selectedAgencyId,
                        accountId: state.selectedAccountId,
                    },
                    queryParamsHandling: 'merge',
                    replaceUrl: true,
                });
            })
        );
    }
}

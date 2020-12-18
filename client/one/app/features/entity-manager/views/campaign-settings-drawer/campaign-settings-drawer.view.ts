import './campaign-settings-drawer.view.less';

import {
    Component,
    Input,
    AfterViewInit,
    OnInit,
    OnDestroy,
    ChangeDetectorRef,
} from '@angular/core';
import {
    CAMPAIGN_TYPES,
    IAB_CATEGORIES,
    LANGUAGES,
    ENTITY_MANAGER_CONFIG,
} from '../../entity-manager.config';
import {CampaignSettingsStore} from '../../services/campaign-settings-store/campaign-settings.store';
import {LevelParam, EntityType, RoutePathName} from '../../../../app.constants';
import * as messagesHelpers from '../../helpers/messages.helpers';
import * as arrayHelpers from '../../../../shared/helpers/array.helpers';
import {Subject, merge, Observable} from 'rxjs';
import {Router} from '@angular/router';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {AuthStore} from '../../../../core/auth/services/auth.store';
import {
    takeUntil,
    map,
    distinctUntilChanged,
    tap,
    filter,
} from 'rxjs/operators';
import {CampaignSettingsStoreState} from '../../services/campaign-settings-store/campaign-settings.store.state';
import {EntityPermissionValue} from '../../../../core/users/users.constants';

@Component({
    selector: 'zem-campaign-settings-drawer',
    templateUrl: './campaign-settings-drawer.view.html',
    providers: [CampaignSettingsStore],
})
export class CampaignSettingsDrawerView
    implements OnInit, OnDestroy, AfterViewInit {
    @Input()
    entityId: string;
    @Input()
    newEntityParentId: string;

    EntityType = EntityType;
    CAMPAIGN_TYPES = CAMPAIGN_TYPES;
    IAB_CATEGORIES = IAB_CATEGORIES;
    LANGUAGES = LANGUAGES;

    isOpen: boolean;
    isNewEntity: boolean;
    isReadOnly: boolean;
    canSeeDeals: boolean = false;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: CampaignSettingsStore,
        public authStore: AuthStore,
        private router: Router,
        private changeDetectorRef: ChangeDetectorRef
    ) {}

    ngOnInit() {
        this.isNewEntity = !this.entityId;
        this.subscribeToStateUpdates();
    }

    ngAfterViewInit() {
        setTimeout(() => {
            this.open();
            if (this.isNewEntity) {
                this.store.loadEntityDefaults(this.newEntityParentId);
            } else {
                this.store.loadEntity(this.entityId);
            }
        }, 1000);
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    open() {
        this.isOpen = true;
        this.changeDetectorRef.detectChanges();
    }

    close() {
        this.isOpen = false;
        this.navigateToRoute([]);
    }

    cancel() {
        let shouldCloseDrawer = true;
        if (this.store.doEntitySettingsHaveUnsavedChanges()) {
            shouldCloseDrawer = confirm(
                messagesHelpers.getClosingUnsavedChangesConfirmMessage()
            );
        }
        if (shouldCloseDrawer) {
            if (this.isNewEntity) {
                this.navigateToRoute([
                    RoutePathName.APP_BASE,
                    RoutePathName.ANALYTICS,
                    LevelParam.ACCOUNT,
                    this.newEntityParentId,
                ]);
            } else {
                this.close();
            }
        }
    }

    async saveSettings() {
        const shouldCloseDrawer = await this.store.saveEntity();
        if (shouldCloseDrawer) {
            if (this.isNewEntity) {
                this.navigateToRoute([
                    RoutePathName.APP_BASE,
                    RoutePathName.ANALYTICS,
                    LevelParam.CAMPAIGN,
                    this.store.state.entity.id,
                ]);
            } else {
                this.close();
            }
        }
    }

    async archive() {
        const shouldReload = await this.store.archiveEntity();
        if (shouldReload) {
            this.navigateToRoute([
                RoutePathName.APP_BASE,
                RoutePathName.ARCHIVED,
                LevelParam.CAMPAIGN,
                this.store.state.entity.id,
            ]);
        }
    }

    canEditBudget(): boolean {
        return this.authStore.hasPermissionOn(
            this.store.state.extras.agencyId,
            this.store.state.entity.accountId,
            EntityPermissionValue.BUDGET
        );
    }

    canAccessPlatformCosts(): boolean {
        return this.authStore.hasPermissionOn(
            this.store.state.extras.agencyId,
            this.store.state.entity.accountId,
            EntityPermissionValue.MEDIA_COST_DATA_COST_LICENCE_FEE
        );
    }

    canAccessAgencyCosts(): boolean {
        return this.authStore.hasPermissionOn(
            this.store.state.extras.agencyId,
            this.store.state.entity.accountId,
            EntityPermissionValue.AGENCY_SPEND_MARGIN
        );
    }

    canSeeServiceFee(): boolean {
        return this.authStore.hasPermissionOn(
            this.store.state.extras.agencyId,
            this.store.state.entity.accountId,
            EntityPermissionValue.BASE_COSTS_SERVICE_FEE
        );
    }

    private navigateToRoute(routePath: string[]) {
        this.isOpen = false;
        this.router
            .navigate(
                [
                    {
                        outlets: {drawer: null},
                    },
                ],
                {
                    queryParams: commonHelpers.getValueWithoutProps(
                        this.router.routerState.root.snapshot.queryParams,
                        [
                            ENTITY_MANAGER_CONFIG.idQueryParam,
                            ENTITY_MANAGER_CONFIG.typeQueryParam,
                        ]
                    ),
                }
            )
            .then(() => {
                if (!arrayHelpers.isEmpty(routePath)) {
                    this.router.navigate(routePath, {
                        queryParamsHandling: 'preserve',
                    });
                }
            });
    }

    private subscribeToStateUpdates() {
        merge(this.createReadOnlyUpdater$(), this.createCanSeeDealsUpdater$())
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe();
    }

    private createReadOnlyUpdater$(): Observable<CampaignSettingsStoreState> {
        return this.store.state$
            .pipe(
                filter(state => commonHelpers.isDefined(state.entity.accountId))
            )
            .pipe(
                map(state => state),
                distinctUntilChanged(),
                tap(state => {
                    this.isReadOnly = this.authStore.hasReadOnlyAccessOn(
                        state.extras.agencyId,
                        state.entity.accountId
                    );
                })
            );
    }

    private createCanSeeDealsUpdater$(): Observable<
        CampaignSettingsStoreState
    > {
        return this.store.state$.pipe(
            tap(state => {
                this.canSeeDeals = this.authStore.hasPermissionOn(
                    state.extras.agencyId,
                    state.entity.accountId,
                    EntityPermissionValue.WRITE
                );
            })
        );
    }
}

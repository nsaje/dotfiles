import './campaign-settings-drawer.view.less';

import {
    Component,
    Input,
    Inject,
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
import {Subject} from 'rxjs';
import {Router} from '@angular/router';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';

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

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: CampaignSettingsStore,
        private router: Router,
        private changeDetectorRef: ChangeDetectorRef,
        @Inject('zemPermissions') public zemPermissions: any
    ) {}

    ngOnInit() {
        this.isNewEntity = !this.entityId;
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

    canAccessPlatformCosts(): boolean {
        return this.zemPermissions.canAccessPlatformCosts();
    }

    canAccessAgencyCosts(): boolean {
        return this.zemPermissions.canAccessAgencyCosts();
    }

    canSeeServiceFee(): boolean {
        return this.zemPermissions.hasPermission('zemauth.can_see_service_fee');
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
}

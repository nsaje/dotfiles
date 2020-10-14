import './ad-group-settings-drawer.view.less';

import {
    AfterViewInit,
    Component,
    Input,
    OnDestroy,
    OnInit,
    ChangeDetectorRef,
} from '@angular/core';
import {
    TARGETING_DEVICE_OPTIONS,
    TARGETING_ENVIRONMENT_OPTIONS,
    TARGETING_CONNECTION_TYPE_OPTIONS,
    ENTITY_MANAGER_CONFIG,
} from '../../entity-manager.config';
import {AdGroupSettingsStore} from '../../services/ad-group-settings-store/ad-group-settings.store';
import {
    Currency,
    EntityType,
    LevelParam,
    RoutePathName,
} from '../../../../app.constants';
import {merge, Observable, Subject} from 'rxjs';
import {
    distinctUntilChanged,
    map,
    takeUntil,
    tap,
    filter,
} from 'rxjs/operators';
import {APP_CONFIG} from '../../../../app.config';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import * as messagesHelpers from '../../helpers/messages.helpers';
import * as arrayHelpers from '../../../../shared/helpers/array.helpers';
import {ImageCheckboxInputGroupItem} from '../../../../shared/components/image-checkbox-input-group/types/image-checkbox-input-group-item';
import {Router} from '@angular/router';
import {AuthStore} from '../../../../core/auth/services/auth.store';
import {AdGroupSettingsStoreState} from '../../services/ad-group-settings-store/ad-group-settings.store.state';
import {
    EXPANDABLE_SECTIONS,
    EXPANDED_SECTIONS_CONFIG,
} from './ad-group-settings-drawer.config';
import {AdGroup} from '../../../../core/entities/types/ad-group/ad-group';
import {ExpandableSection} from './ad-group-settings.drawer.constants';

@Component({
    selector: 'zem-ad-group-settings-drawer',
    templateUrl: './ad-group-settings-drawer.view.html',
    providers: [AdGroupSettingsStore],
})
export class AdGroupSettingsDrawerView
    implements OnInit, AfterViewInit, OnDestroy {
    @Input()
    entityId: string;
    @Input()
    newEntityParentId: string;

    EntityType = EntityType;

    isOpen = false;
    isNewEntity = false;
    isReadOnly: boolean;
    minEndDate = new Date();
    currencySymbol = '';

    targetingDeviceOptions: ImageCheckboxInputGroupItem[] = TARGETING_DEVICE_OPTIONS;
    targetingEnvironmentOptions: ImageCheckboxInputGroupItem[] = TARGETING_ENVIRONMENT_OPTIONS;
    targetingConnectionTypeOptions: ImageCheckboxInputGroupItem[] = TARGETING_CONNECTION_TYPE_OPTIONS;

    expandableSection = ExpandableSection;

    expandedSectionsByDefault: {[key in ExpandableSection]: boolean} = {
        [ExpandableSection.SCHEDULING]: false,
        [ExpandableSection.BUDGET]: false,
        [ExpandableSection.DEVICE_TARGETING]: false,
        [ExpandableSection.GEOTARGETING]: false,
        [ExpandableSection.TRACKING]: false,
        [ExpandableSection.AUDIENCE]: false,
    };

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: AdGroupSettingsStore,
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
                this.store
                    .loadEntityDefaults(this.newEntityParentId)
                    .then(() => {
                        this.expandedSectionsByDefault = this.getExpandedSectionsByDefault(
                            this.store.state.entity
                        );
                    });
            } else {
                this.store.loadEntity(this.entityId).then(() => {
                    this.expandedSectionsByDefault = this.getExpandedSectionsByDefault(
                        this.store.state.entity
                    );
                });
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
                    LevelParam.CAMPAIGN,
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
                    LevelParam.AD_GROUP,
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
                LevelParam.AD_GROUP,
                this.store.state.entity.id,
            ]);
        }
    }

    private subscribeToStateUpdates() {
        merge(
            this.createCurrencySymbolUpdater$(),
            this.createReadOnlyUpdater$()
        )
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe();
    }

    private createCurrencySymbolUpdater$(): Observable<Currency> {
        return this.store.state$.pipe(
            map(state => state.extras.currency),
            distinctUntilChanged(),
            tap(currency => {
                this.currencySymbol = APP_CONFIG.currencySymbols[currency];
            })
        );
    }

    private createReadOnlyUpdater$(): Observable<AdGroupSettingsStoreState> {
        return this.store.state$
            .pipe(
                filter(state => commonHelpers.isDefined(state.extras.accountId))
            )
            .pipe(
                map(state => state),
                distinctUntilChanged(),
                tap(state => {
                    this.isReadOnly = this.authStore.hasReadOnlyAccessOn(
                        state.extras.agencyId,
                        state.extras.accountId
                    );
                })
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

    private getExpandedSectionsByDefault(
        entity: AdGroup
    ): {[key in ExpandableSection]: boolean} {
        const expandedSectionsByDefault = {} as {
            [key in ExpandableSection]: boolean;
        };
        EXPANDABLE_SECTIONS.forEach(section => {
            expandedSectionsByDefault[section] = EXPANDED_SECTIONS_CONFIG[
                section
            ](entity);
        });
        return expandedSectionsByDefault;
    }
}

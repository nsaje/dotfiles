import './ad-group-settings-drawer.view.less';

import {
    Component,
    Input,
    Inject,
    AfterViewInit,
    OnDestroy,
    OnInit,
} from '@angular/core';
import {ENTITY_MANAGER_CONFIG} from '../../entity-manager.config';
import {AdGroupSettingsStore} from '../../services/ad-group-settings.store';
import {LevelStateParam} from '../../../../app.constants';
import {Subject} from 'rxjs';
import {takeUntil, map, distinctUntilChanged} from 'rxjs/operators';
import {APP_CONFIG} from '../../../../app.config';

@Component({
    selector: 'zem-ad-group-settings-drawer',
    templateUrl: './ad-group-settings-drawer.view.html',
    providers: [AdGroupSettingsStore],
})
export class AdGroupSettingsDrawerView
    implements OnInit, AfterViewInit, OnDestroy {
    @Input()
    entityId: number;
    @Input()
    newEntityParentId: number;

    isOpen = false;
    isNewEntity = false;
    minEndDate = new Date();
    currencySymbol = '';

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: AdGroupSettingsStore,
        @Inject('zemPermissions') public zemPermissions: any,
        @Inject('ajs$state') private ajs$state: any,
        @Inject('ajs$location') private ajs$location: any
    ) {}

    ngOnInit() {
        this.isNewEntity = !this.entityId;

        this.subscribeToCurrencyUpdates();
    }

    ngAfterViewInit() {
        if (this.isNewEntity) {
            this.store.loadEntityDefaults(this.newEntityParentId);
        } else {
            this.store.loadEntity(this.entityId);
        }

        setTimeout(() => {
            this.open();
        });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    open() {
        this.isOpen = true;
    }

    close() {
        this.isOpen = false;
        setTimeout(() => {
            this.ajs$location
                .search(ENTITY_MANAGER_CONFIG.settingsQueryParam, null)
                .replace();
        }, 250);
    }

    cancel() {
        let shouldCloseDrawer = true;
        if (this.store.doEntitySettingsHaveUnsavedChanges()) {
            shouldCloseDrawer = confirm(
                'You have unsaved changes.\nAre you sure you want to close settings?'
            );
        }
        if (shouldCloseDrawer) {
            if (this.isNewEntity) {
                this.redirectToParentAnalyticsView(this.newEntityParentId);
            } else {
                this.close();
            }
        }
    }

    async saveSettings() {
        const shouldCloseDrawer = await this.store.saveEntity();
        if (shouldCloseDrawer) {
            if (this.isNewEntity) {
                this.redirectToNewEntityAnalyticsView(
                    this.store.state.entity.id
                );
            } else {
                this.close();
            }
        }
    }

    archive() {
        this.store.archiveEntity();
    }

    private subscribeToCurrencyUpdates() {
        this.store.state$
            .pipe(
                map(state => state.extras.currency),
                distinctUntilChanged(),
                takeUntil(this.ngUnsubscribe$)
            )
            .subscribe(currency => {
                this.currencySymbol = APP_CONFIG.currencySymbols[currency];
            });
    }

    private redirectToNewEntityAnalyticsView(newEntityId: number) {
        this.redirectToEntityView(LevelStateParam.AD_GROUP, newEntityId);
    }

    private redirectToParentAnalyticsView(parentId: number) {
        this.redirectToEntityView(LevelStateParam.CAMPAIGN, parentId);
    }

    private redirectToEntityView(level: LevelStateParam, entityId: number) {
        const url = this.ajs$state.href('v2.analytics', {
            level: level,
            id: entityId,
        });
        this.ajs$location.url(url);
    }
}

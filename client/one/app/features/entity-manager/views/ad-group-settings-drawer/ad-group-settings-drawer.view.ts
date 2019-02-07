import './ad-group-settings-drawer.view.less';

import {Component, Input, Inject, AfterViewInit} from '@angular/core';
import {ENTITY_MANAGER_CONFIG} from '../../entity-manager.config';
import {AdGroupSettingsStore} from '../../services/ad-group-settings.store';
import {LevelStateParam} from '../../../../app.constants';

@Component({
    selector: 'zem-ad-group-settings-drawer',
    templateUrl: './ad-group-settings-drawer.view.html',
    providers: [AdGroupSettingsStore],
})
export class AdGroupSettingsDrawerView implements AfterViewInit {
    @Input()
    entityId: number;
    @Input()
    newEntityParentId: number;

    isOpen: boolean;
    isNewEntity: boolean;

    constructor(
        public store: AdGroupSettingsStore,
        @Inject('ajs$state') private ajs$state: any,
        @Inject('ajs$location') private ajs$location: any
    ) {}

    ngAfterViewInit() {
        this.isNewEntity = !this.entityId;
        if (this.isNewEntity) {
            this.store.loadEntityDefaults(this.newEntityParentId);
        } else {
            this.store.loadEntity(this.entityId);
        }

        setTimeout(() => {
            this.open();
        });
    }

    open() {
        this.isOpen = true;
    }

    cancel() {
        if (this.isNewEntity) {
            const url = this.ajs$state.href('v2.analytics', {
                level: LevelStateParam.CAMPAIGN,
                id: this.newEntityParentId,
            });
            return this.ajs$location.url(url);
        }

        this.isOpen = false;
        setTimeout(() => {
            this.ajs$location
                .search(ENTITY_MANAGER_CONFIG.settingsQueryParam, null)
                .replace();
        }, 250);
    }

    async saveSettings() {
        const shouldCloseDrawer = await this.store.saveEntity();
        if (shouldCloseDrawer) {
            this.cancel();
        }
    }

    archive() {
        this.store.archiveEntity();
    }
}

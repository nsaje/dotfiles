import './campaign-settings-drawer.view.less';

import {Component, Input, Inject, AfterViewInit} from '@angular/core';
import {ENTITY_MANAGER_CONFIG} from '../../entity-manager.config';

@Component({
    selector: 'zem-campaign-settings-drawer',
    templateUrl: './campaign-settings-drawer.view.html',
})
export class CampaignSettingsDrawerView implements AfterViewInit {
    @Input()
    entityId: number;

    isOpen: boolean;

    constructor(@Inject('ajs$location') private ajs$location: any) {}

    ngAfterViewInit() {
        setTimeout(() => {
            this.open();
        });
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
}

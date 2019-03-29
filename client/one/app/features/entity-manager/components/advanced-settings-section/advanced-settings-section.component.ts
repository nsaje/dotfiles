import './advanced-settings-section.component.less';

import {Component, ChangeDetectionStrategy} from '@angular/core';

@Component({
    selector: 'zem-advanced-settings-section',
    templateUrl: './advanced-settings-section.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdvancedSettingsSectionComponent {
    expanded = false;

    toggle() {
        this.expanded = !this.expanded;
    }
}

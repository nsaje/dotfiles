import './advanced-settings-section.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    OnChanges,
    SimpleChanges,
} from '@angular/core';

@Component({
    selector: 'zem-advanced-settings-section',
    templateUrl: './advanced-settings-section.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdvancedSettingsSectionComponent implements OnChanges {
    @Input()
    expandedByDefault: boolean;
    @Input()
    overviewText: string;
    @Input()
    customLabelCollapsed: string;
    @Input()
    customLabelExpanded: string;

    expanded = false;

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.expandedByDefault) {
            this.expanded = this.expandedByDefault || this.expanded;
        }
    }

    toggle() {
        this.expanded = !this.expanded;
    }
}

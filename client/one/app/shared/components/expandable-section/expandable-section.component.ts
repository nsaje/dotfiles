import './expandable-section.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    OnChanges,
    SimpleChanges,
} from '@angular/core';

@Component({
    selector: 'zem-expandable-section',
    templateUrl: './expandable-section.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ExpandableSectionComponent implements OnChanges {
    @Input()
    expandedByDefault: boolean;
    @Input()
    expandLabel: string = 'Show';
    @Input()
    collapseLabel: string = 'Hide';

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

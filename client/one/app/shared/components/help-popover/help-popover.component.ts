import './help-popover.component.less';

import {Component, Input, ChangeDetectionStrategy} from '@angular/core';

@Component({
    selector: 'zem-help-popover',
    templateUrl: './help-popover.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HelpPopoverComponent {
    @Input()
    content: string;
    @Input()
    placement: string = 'top';
}

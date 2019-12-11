import './content-form-group.component.less';

import {
    Component,
    OnChanges,
    ChangeDetectionStrategy,
    SimpleChanges,
    EventEmitter,
    Output,
    Input,
} from '@angular/core';

@Component({
    selector: 'zem-content-form-group',
    templateUrl: './content-form-group.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ContentFormGroupComponent {
    @Input()
    label: string;
    @Input()
    helpMessage: string;
}

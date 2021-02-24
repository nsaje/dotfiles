import './form-field-with-sidebar.component.less';

import {
    ChangeDetectionStrategy,
    Component,
    EventEmitter,
    Input,
    Output,
} from '@angular/core';

@Component({
    selector: 'zem-form-field-with-sidebar',
    templateUrl: './form-field-with-sidebar.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormFieldWithSidebarComponent {
    @Input()
    length: number = 0;
    @Input()
    maxLength: number;
    @Output()
    useAsDefaultClick: EventEmitter<void> = new EventEmitter<void>();
}

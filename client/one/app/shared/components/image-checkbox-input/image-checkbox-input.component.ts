import './image-checkbox-input.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {ImageCheckboxInputItem} from './types/image-checkbox-input-item';

@Component({
    selector: 'zem-image-checkbox-input',
    templateUrl: './image-checkbox-input.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ImageCheckboxInputComponent {
    @Input()
    value: ImageCheckboxInputItem;
    @Input()
    isDisabled: boolean;
    @Output()
    itemToggled: EventEmitter<String> = new EventEmitter<String>();
}

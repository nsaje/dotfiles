import './alert.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {AlertStyleClass} from './alert.component.constants';

@Component({
    selector: 'zem-alert',
    templateUrl: './alert.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AlertComponent {
    @Input()
    styleClass: AlertStyleClass;
    @Input()
    isClosable: boolean;
    @Output()
    close = new EventEmitter<void>();
}

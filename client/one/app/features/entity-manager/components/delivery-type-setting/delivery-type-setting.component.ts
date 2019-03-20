import './delivery-type-setting.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    Output,
    Input,
} from '@angular/core';
import {DeliveryType} from '../../../../app.constants';

@Component({
    selector: 'zem-delivery-type-setting',
    templateUrl: './delivery-type-setting.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DeliveryTypeSettingComponent {
    @Input()
    value: DeliveryType;
    @Input()
    errors: string[];
    @Output()
    valueChange = new EventEmitter<DeliveryType>();

    DeliveryType = DeliveryType;

    onSelect($event: DeliveryType) {
        this.valueChange.emit($event);
    }
}

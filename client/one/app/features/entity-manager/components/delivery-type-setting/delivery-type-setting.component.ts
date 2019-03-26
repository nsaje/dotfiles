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
    deliveryType: DeliveryType;
    @Input()
    errors: string[];
    @Output()
    valueChange = new EventEmitter<DeliveryType>();

    DeliveryType = DeliveryType;

    onSelect($event: DeliveryType) {
        this.valueChange.emit($event);
    }

    hasStandardDeliveryTypeErrors(): boolean {
        return (
            this.deliveryType === DeliveryType.STANDARD &&
            this.errors &&
            this.errors.length > 0
        );
    }

    hasAcceleratedDeliveryTypeErrors(): boolean {
        return (
            this.deliveryType === DeliveryType.ACCELERATED &&
            this.errors &&
            this.errors.length > 0
        );
    }
}

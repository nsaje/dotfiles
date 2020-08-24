import './tracking-code-setting.component.less';

import {
    Component,
    OnChanges,
    ChangeDetectionStrategy,
    SimpleChanges,
    EventEmitter,
    Output,
    Input,
    OnInit,
} from '@angular/core';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';

@Component({
    selector: 'zem-tracking-code-setting',
    templateUrl: './tracking-code-setting.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TrackingCodeSettingComponent implements OnInit, OnChanges {
    @Input()
    value: string;
    @Input()
    rows: number;
    @Input()
    isDisabled: boolean = false;
    @Input()
    isFocused: boolean = false;
    @Input()
    @Input()
    errors: string[];
    @Output()
    valueChange = new EventEmitter<string>();

    model: string;

    ngOnInit(): void {
        this.rows = commonHelpers.getValueOrDefault(this.rows, 4);
    }

    ngOnChanges(changes: SimpleChanges) {
        if (changes.value) {
            this.model = this.value;
        }
    }

    onBlur($event: string) {
        this.valueChange.emit($event);
    }
}

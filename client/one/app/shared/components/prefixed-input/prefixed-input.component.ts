import './prefixed-input.component.less';

import {Component, ChangeDetectionStrategy, Input} from '@angular/core';

@Component({
    selector: 'zem-prefixed-input',
    templateUrl: './prefixed-input.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PrefixedInputComponent {
    @Input()
    prefix: string;
    @Input()
    hasError: boolean;
}

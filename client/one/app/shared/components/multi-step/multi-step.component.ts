import './multi-step.component.less';

import {
    ChangeDetectionStrategy,
    Component,
    ContentChildren,
    Input,
    QueryList,
} from '@angular/core';
import {MultiStepStepDirective} from './multi-step-step.directive';

@Component({
    selector: 'zem-multi-step',
    templateUrl: './multi-step.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MultiStepComponent {
    @ContentChildren(MultiStepStepDirective)
    steps: QueryList<MultiStepStepDirective>;

    @Input()
    currentStep: number = 0;
    @Input()
    animated: boolean = true;
}

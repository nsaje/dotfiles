import './hacks.component.less';

import {Component, ChangeDetectionStrategy, Input} from '@angular/core';
import {Hack} from '../../../../core/entities/types/common/hack';
import {HackLevel} from '../../../../app.constants';

@Component({
    selector: 'zem-hacks',
    templateUrl: './hacks.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HacksComponent {
    @Input()
    hacks: Hack[];

    showOnlyNonGlobal: boolean = true;
    HackLevel = HackLevel;
}

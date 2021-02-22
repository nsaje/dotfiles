import './trackers-form-group.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {Tracker} from '../../../../../core/creatives/types/tracker';
import {TrackerErrors} from '../../types/tracker-errors';

@Component({
    selector: 'zem-trackers-form-group',
    templateUrl: './trackers-form-group.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TrackersFormGroupComponent {
    @Input()
    label: string;
    @Input()
    helpMessage: string;
    @Input()
    value: Tracker[];
    @Input()
    errors: TrackerErrors[];
    @Input()
    isDisabled: boolean;
    @Input()
    isLoading: boolean = false;
    @Input()
    canUseExtraTrackers: boolean = false;
    @Output()
    valueChange: EventEmitter<Tracker[]> = new EventEmitter<Tracker[]>();
}

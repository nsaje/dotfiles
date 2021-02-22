import './tracker.component.less';
import {
    Input,
    Output,
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    OnChanges,
} from '@angular/core';
import {Tracker} from '../../../../../core/creatives/types/tracker';
import {TRACKER_EVENT_TYPE_NAMES} from '../../creatives-shared.config';
import {TrackerErrors} from '../../types/tracker-errors';
import * as commonHelpers from '../../../../../shared/helpers/common.helpers';

@Component({
    selector: 'zem-tracker',
    templateUrl: './tracker.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TrackerComponent implements OnChanges {
    @Input()
    tracker: Tracker;
    @Input()
    trackerErrors: TrackerErrors;
    @Input()
    isDisabled: boolean = false;
    @Input()
    index: number;
    @Output()
    trackerRemove: EventEmitter<void> = new EventEmitter<void>();

    trackerEventTypeNames = TRACKER_EVENT_TYPE_NAMES;

    isEditFormVisible: boolean = false;

    ngOnChanges(): void {
        if (this.hasErrors(this.trackerErrors) || !this.tracker?.url) {
            this.isEditFormVisible = true;
        }
    }

    private hasErrors(trackerErrors: TrackerErrors) {
        return (
            commonHelpers.isDefined(trackerErrors) &&
            Object.values(trackerErrors).some(e => e)
        );
    }
}

import './publisher-group-edit-form.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {PublisherGroup} from './types/publisher-group';
import {ChangeEvent} from '../../types/change-event';
import {PublisherGroupErrors} from './types/publisher-group-errors';

@Component({
    selector: 'zem-publisher-group-edit-form',
    templateUrl: './publisher-group-edit-form.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PublisherGroupEditFormComponent {
    @Input()
    publisherGroup: PublisherGroup;
    @Input()
    publisherGroupErrors: PublisherGroupErrors;
    @Input()
    isDisabled: boolean = false;
    @Input()
    showFileUpload: boolean = true;
    @Output()
    publisherGroupChange = new EventEmitter<ChangeEvent<PublisherGroup>>();
    @Output()
    downloadErrors = new EventEmitter<void>();
    @Output()
    downloadExample = new EventEmitter<void>();

    onNameChange(name: string) {
        this.publisherGroupChange.emit({
            target: this.publisherGroup,
            changes: {
                name: name,
            },
        });
    }

    onIncludeSubdomainsChange(includeSubdomains: boolean) {
        this.publisherGroupChange.emit({
            target: this.publisherGroup,
            changes: {
                includeSubdomains: includeSubdomains,
            },
        });
    }

    onEntriesChange(files: File[]) {
        const entries: File = files.length === 1 ? files[0] : null;
        this.publisherGroupChange.emit({
            target: this.publisherGroup,
            changes: {
                entries: entries,
            },
        });
    }
}

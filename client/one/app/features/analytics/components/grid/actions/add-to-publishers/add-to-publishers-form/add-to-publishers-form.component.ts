import './add-to-publishers-form.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    EventEmitter,
    Output,
} from '@angular/core';
import {PublisherGroup} from '../../../../../../../core/publisher-groups/types/publisher-group';
import {PublisherGroupFieldsErrorsState} from '../../../../../../publisher-groups/types/publisher-group-fields-errors-state';

@Component({
    selector: 'zem-add-to-publishers-form',
    templateUrl: './add-to-publishers-form.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AddToPublishersFormComponent {
    @Input()
    availablePublisherGroups: PublisherGroup[];
    @Input()
    publisherGroup: PublisherGroup;
    @Input()
    publisherGroupErrors: PublisherGroupFieldsErrorsState;
    @Input()
    searchInProgress: boolean;

    @Output()
    search: EventEmitter<string> = new EventEmitter<string>();
    @Output()
    publisherGroupSelected: EventEmitter<PublisherGroup> = new EventEmitter<
        PublisherGroup
    >();
    @Output()
    switchToCreate: EventEmitter<void> = new EventEmitter<void>();

    selectPublisherGroup(publisherGroupId: string) {
        this.publisherGroupSelected.emit(
            this.availablePublisherGroups.find(
                publisherGroup => publisherGroup.id === publisherGroupId
            )
        );
    }
}

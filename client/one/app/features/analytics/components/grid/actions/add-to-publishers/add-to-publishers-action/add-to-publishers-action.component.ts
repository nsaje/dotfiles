import './add-to-publishers-action.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    ViewChild,
    Input,
    Output,
    EventEmitter,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {ModalComponent} from '../../../../../../../shared/components/modal/modal.component';
import {PublisherInfo} from '../../../../../../../core/publishers/types/publisher-info';
import {AddToPublishersActionStore} from './services/add-to-publishers-action.store';
import {isEmpty} from '../../../../../../../shared/helpers/array.helpers';
import {equalsIgnoreCase} from '../../../../../../../shared/helpers/string.helpers';
import {GRID_ITEM_NOT_REPORTED} from '../../../../../analytics.constants';

@Component({
    selector: 'zem-add-to-publishers-action',
    templateUrl: './add-to-publishers-action.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [AddToPublishersActionStore],
})
export class AddToPublishersActionComponent implements OnChanges {
    @Input()
    selectedRows: PublisherInfo[];
    @Input()
    accountId: number;
    @Output()
    actionSuccess: EventEmitter<boolean> = new EventEmitter<boolean>();

    @ViewChild(ModalComponent, {static: false})
    addToPublishersModal: ModalComponent;

    buttonDisabled: boolean = true;
    filteredSelectedRows: PublisherInfo[] = [];

    constructor(public store: AddToPublishersActionStore) {}

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.selectedRows) {
            this.filteredSelectedRows = this.selectedRows.filter(
                row => !equalsIgnoreCase(row.placement, GRID_ITEM_NOT_REPORTED)
            );
            this.buttonDisabled = isEmpty(this.filteredSelectedRows);
        }
    }

    search(keyword: string) {
        this.store.search(this.accountId.toString(), keyword);
    }

    save() {
        this.store
            .save(this.accountId.toString(), this.filteredSelectedRows)
            .then(() => {
                this.actionSuccess.emit(true);
                this.close();
            });
    }

    close() {
        this.addToPublishersModal.close();
        this.store.reset();
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemAddToPublishersAction',
    downgradeComponent({
        component: AddToPublishersActionComponent,
        propagateDigest: false,
    })
);

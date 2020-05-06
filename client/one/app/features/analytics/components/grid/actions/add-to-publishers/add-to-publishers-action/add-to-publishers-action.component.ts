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
    ElementRef,
    ChangeDetectorRef,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {ModalComponent} from '../../../../../../../shared/components/modal/modal.component';
import {PublisherInfo} from '../../../../../../../core/publishers/types/publisher-info';
import {AddToPublishersActionStore} from './services/add-to-publishers-action.store';
import {isEmpty} from '../../../../../../../shared/helpers/array.helpers';

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

    constructor(public store: AddToPublishersActionStore) {}

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.selectedRows) {
            this.buttonDisabled = isEmpty(this.selectedRows);
        }
    }

    search(keyword: string) {
        this.store.search(this.accountId.toString(), keyword);
    }

    save() {
        this.store
            .save(this.accountId.toString(), this.selectedRows)
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

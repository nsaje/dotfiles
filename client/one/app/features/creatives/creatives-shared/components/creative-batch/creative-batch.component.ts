import './creative-batch.component.less';
import {
    ChangeDetectionStrategy,
    Component,
    Input,
    OnChanges,
} from '@angular/core';
import {CreativeBatchStore} from '../../services/creative-batch-store/creative-batch.store';
import {FetchCreativeBatchActionEffect} from '../../services/creative-batch-store/effects/fetch-creative-batch.effect';
import {CreateCreativeBatchActionEffect} from '../../services/creative-batch-store/effects/create-creative-batch.effect';
import {EditCreativeBatchActionEffect} from '../../services/creative-batch-store/effects/edit-creative-batch.effect';
import {ValidateCreativeBatchActionEffect} from '../../services/creative-batch-store/effects/validate-creative-batch.effect';
import {isDefined} from '../../../../../shared/helpers/common.helpers';

@Component({
    selector: 'zem-creative-batch',
    templateUrl: './creative-batch.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [
        CreativeBatchStore,
        CreateCreativeBatchActionEffect,
        EditCreativeBatchActionEffect,
        FetchCreativeBatchActionEffect,
        ValidateCreativeBatchActionEffect,
    ],
})
export class CreativeBatchComponent implements OnChanges {
    @Input()
    batchId: string;

    constructor(public store: CreativeBatchStore) {}

    ngOnChanges() {
        if (isDefined(this.batchId)) {
            this.store.loadEntity(this.batchId);
        }
    }
}

import './bid-modifier-cell.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnChanges,
    SimpleChanges,
    Input,
    Output,
    EventEmitter,
    OnInit,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import * as clone from 'clone';
import {
    EditableCellMode,
    EditableCellPlacement,
} from '../editable-cell/editable-cell.constants';
import {BidModifierCellStore} from './services/bid-modifier-cell.store';
import {BidModifier} from '../../../../../core/bid-modifiers/types/bid-modifier';
import {BidModifiersService} from '../../../../../core/bid-modifiers/services/bid-modifiers.service';
import {BID_MODIFIER_CELL_CONFIG} from './bid-modifier-cell.config';
import {KeyCode, Currency} from '../../../../../app.constants';

@Component({
    selector: 'zem-bid-modifier-cell',
    templateUrl: './bid-modifier-cell.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [BidModifierCellStore, BidModifiersService],
})
export class BidModifierCellComponent implements OnInit, OnChanges {
    @Input()
    bidModifier: BidModifier;
    @Input()
    entityId: number;
    @Input()
    currency: Currency;
    @Input()
    isEditable: boolean;
    @Input()
    editMessage: string;
    @Input()
    showAutopilotIcon: boolean;
    @Input()
    containerElement: HTMLElement;
    @Output()
    valueChange = new EventEmitter<BidModifier>();

    mode: EditableCellMode;
    EditableCellMode = EditableCellMode;

    placement: EditableCellPlacement;
    EditableCellPlacement = EditableCellPlacement;

    fractionSize: number;

    constructor(public store: BidModifierCellStore) {}

    ngOnInit(): void {
        this.mode = EditableCellMode.READ;
        this.placement = EditableCellPlacement.IN_LINE;
        this.fractionSize = BID_MODIFIER_CELL_CONFIG.fractionSize;
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.bidModifier && this.bidModifier) {
            this.store.loadBidModifier(
                this.bidModifier,
                this.entityId,
                this.currency
            );
        }
    }

    onValueChange($event: string) {
        this.store.updateBidModifier($event);
    }

    save(): void {
        this.store
            .saveBidModifier()
            .then((response: BidModifier) => {
                this.mode = EditableCellMode.READ;
                this.valueChange.emit(clone(response));
            })
            .catch(() => {});
    }

    cancel(): void {
        this.mode = EditableCellMode.READ;
        this.store.updateBidModifier(this.store.state.previousModifierPercent);
    }

    onModeChange($event: EditableCellMode) {
        this.mode = $event;
        if ($event === EditableCellMode.READ) {
            this.store.updateBidModifier(
                this.store.state.previousModifierPercent
            );
        }
    }

    onPlacementChange($event: EditableCellPlacement) {
        this.placement = $event;
    }

    onInputKeydown($event: KeyboardEvent) {
        if ($event.keyCode === KeyCode.ENTER) {
            this.save();
        }
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemBidModifierCell',
    downgradeComponent({
        component: BidModifierCellComponent,
    })
);

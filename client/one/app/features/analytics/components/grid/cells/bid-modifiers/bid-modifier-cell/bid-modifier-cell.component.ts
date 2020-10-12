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
} from '../../editable-cell/editable-cell.constants';
import {BidModifierCellStore} from './services/bid-modifier-cell.store';
import {BidModifier} from '../../../../../../../core/bid-modifiers/types/bid-modifier';
import {BidModifiersService} from '../../../../../../../core/bid-modifiers/services/bid-modifiers.service';
import {
    KeyCode,
    Currency,
    BiddingType,
    AdGroupAutopilotState,
} from '../../../../../../../app.constants';
import {BidModifierTypeSummary} from '../../../../../../../core/bid-modifiers/types/bid-modifier-type-summary';
import {EditableCellApi} from '../../editable-cell/types/editable-cell-api';
import * as commonHelpers from '../../../../../../../shared/helpers/common.helpers';

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
    biddingType: BiddingType;
    @Input()
    bid: string;
    @Input()
    bidModifierTypeSummaries: BidModifierTypeSummary[];
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
    adGroupAutopilotState: AdGroupAutopilotState;
    @Input()
    containerElement: HTMLElement;
    @Input()
    agencyUsesRealtimeAutopilot: boolean = false;
    @Output()
    valueChange = new EventEmitter<BidModifier>();

    mode: EditableCellMode;
    EditableCellMode = EditableCellMode;

    placement: EditableCellPlacement;
    EditableCellPlacement = EditableCellPlacement;

    editableCellApi: EditableCellApi;

    constructor(public store: BidModifierCellStore) {}

    ngOnInit(): void {
        this.mode = EditableCellMode.READ;
        this.placement = EditableCellPlacement.IN_LINE;
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

    onEditableCellReady($event: EditableCellApi) {
        this.editableCellApi = $event;
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

    showDetails() {
        if (commonHelpers.isDefined(this.editableCellApi)) {
            this.editableCellApi.expandAsModal();
        }
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemBidModifierCell',
    downgradeComponent({
        component: BidModifierCellComponent,
        propagateDigest: false,
    })
);

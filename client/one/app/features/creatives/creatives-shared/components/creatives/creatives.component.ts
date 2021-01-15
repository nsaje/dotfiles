import './creatives.component.less';

import {
    ChangeDetectionStrategy,
    Component,
    EventEmitter,
    Input,
    OnChanges,
    Output,
    SimpleChanges,
} from '@angular/core';
import {ScopeParams} from '../../../../../shared/types/scope-params';
import {CreativesSearchParams} from '../../types/creatives-search-params';
import {PaginationState} from '../../../../../shared/components/smart-grid/types/pagination-state';
import {CreativesStore} from '../../services/creatives-store/creatives.store';
import {PaginationOptions} from '../../../../../shared/components/smart-grid/types/pagination-options';
import {DEFAULT_PAGINATION_OPTIONS} from '../../creatives-shared.config';
import * as deepEqual from 'fast-deep-equal';
import {FetchCreativesActionEffect} from '../../services/creatives-store/effects/fetch-creatives.effect';
import {isDefined} from '../../../../../shared/helpers/common.helpers';

@Component({
    selector: 'zem-creatives',
    templateUrl: './creatives.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [CreativesStore, FetchCreativesActionEffect],
})
export class CreativesComponent implements OnChanges {
    @Input()
    scopeParams: ScopeParams;
    @Input()
    searchParams: CreativesSearchParams;
    @Input()
    pagination: PaginationState;
    @Output()
    searchParamsChange: EventEmitter<CreativesSearchParams> = new EventEmitter<
        CreativesSearchParams
    >();
    @Output()
    paginationChange: EventEmitter<PaginationState> = new EventEmitter<
        PaginationState
    >();

    context: any;
    isReadOnly: boolean = true;
    paginationOptions: PaginationOptions = DEFAULT_PAGINATION_OPTIONS;
    availableTags: string[] = ['a', 'b', 'c']; // TODO: retrieve this from backend

    constructor(public store: CreativesStore) {
        this.context = {
            componentParent: this,
        };
    }

    ngOnChanges(changes: SimpleChanges): void {
        this.paginationOptions = {
            ...DEFAULT_PAGINATION_OPTIONS,
            ...this.pagination,
        };

        if (isDefined(this.scopeParams?.agencyId)) {
            if (!deepEqual(this.scopeParams, this.store.state.scope)) {
                this.store.setStore(
                    this.scopeParams,
                    this.pagination,
                    this.searchParams
                );
            } else {
                this.store.loadEntities(this.pagination, this.searchParams);
            }
        }
    }
}

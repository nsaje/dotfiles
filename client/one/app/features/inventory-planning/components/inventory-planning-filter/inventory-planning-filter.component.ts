import './inventory-planning-filter.component.less';

import {Component, Input, Output, EventEmitter, OnChanges, ChangeDetectionStrategy} from '@angular/core';

import {SelectedFilters} from '../../types/selected-filters';
import {SelectedFilterOption} from '../../types/selected-filter-option';


@Component({
    selector: 'zem-inventory-planning-filter',
    template: require('./inventory-planning-filter.component.html'),
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InventoryPlanningFilterComponent implements OnChanges {
    @Input() selected: SelectedFilters;
    @Output() onRemove = new EventEmitter<{key: string, value: string}>();

    isFilterEnabled: boolean;
    isCountryFilterEnabled: boolean;
    isPublisherFilterEnabled: boolean;
    isDeviceFilterEnabled: boolean;

    ngOnChanges (changes: any) {
        if (changes.selected) {
            this.isCountryFilterEnabled = this.selected.countries.length !== 0;
            this.isPublisherFilterEnabled = this.selected.publishers.length !== 0;
            this.isDeviceFilterEnabled = this.selected.devices.length !== 0;
            this.isFilterEnabled =
                this.isCountryFilterEnabled || this.isPublisherFilterEnabled || this.isDeviceFilterEnabled;
        }
    }

    removeFilterOption (list: SelectedFilterOption[], value: string): void {
        Object.keys(this.selected).forEach(key => {
            if (this.selected[key] === list) {
                this.onRemove.emit({key, value});
            }
        });
    }
}

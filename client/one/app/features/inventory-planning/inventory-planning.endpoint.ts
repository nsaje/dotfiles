import {Injectable} from '@angular/core';
import {Observable} from 'rxjs/Observable';
import 'rxjs/add/observable/of';
import 'rxjs/add/operator/delay';

import {Inventory} from './types/inventory';
import {AvailableFilterOption} from './types/available-filter-option';
import {SelectedFilters} from './types/selected-filters';

@Injectable()
export class InventoryPlanningEndpoint {
    loadSummary (selectedFilters: SelectedFilters): Observable<Inventory> {
        return Observable.of({
            auctionCount: Math.floor(Math.random() * 10000000), // tslint:disable-line
            avgCpm: Math.random() * 5, // tslint:disable-line
        }).delay(5000); // tslint:disable-line
    }

    loadCountries (selectedFilters: SelectedFilters): Observable<AvailableFilterOption[]> {
        return Observable.of(this.generateOptions('country', 280)).delay(3000); // tslint:disable-line
    }

    loadPublishers (selectedFilters: SelectedFilters): Observable<AvailableFilterOption[]> {
        return Observable.of(this.generateOptions('publisher', 20001)).delay(4000); // tslint:disable-line
    }

    loadDevices (selectedFilters: SelectedFilters): Observable<AvailableFilterOption[]> {
        return Observable.of(this.generateOptions('device', 3)).delay(2000); // tslint:disable-line
    }

    private generateOptions (type: string, n: number): AvailableFilterOption[] {
        const options: AvailableFilterOption[] = [];
        for (let i = 0; i < n; i++) {
            options.push({value: i.toString(), name: `Test ${type} no. ${i + 1}`, auctionCount: 100000000 - i * 100000}); // tslint:disable-line
        }
        return options;
    }
}

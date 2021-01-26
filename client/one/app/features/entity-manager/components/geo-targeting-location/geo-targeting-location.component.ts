import './geo-targeting-location.component.less';

import {
    Input,
    Output,
    EventEmitter,
    Component,
    ChangeDetectionStrategy,
} from '@angular/core';
import {Geolocation} from '../../../../core/geolocations/types/geolocation';

@Component({
    selector: 'zem-geo-targeting-location',
    templateUrl: './geo-targeting-location.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class GeoTargetingLocationComponent {
    @Input()
    location: Geolocation;
    @Input()
    highlightText: string = '';
    @Input()
    canRemoveLocation: boolean = true;
    @Output()
    removeLocation: EventEmitter<Geolocation> = new EventEmitter<Geolocation>();
}

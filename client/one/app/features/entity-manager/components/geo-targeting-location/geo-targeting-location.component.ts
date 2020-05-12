import './geo-targeting-location.component.less';

import {
    Input,
    Output,
    EventEmitter,
    Component,
    ChangeDetectionStrategy,
    OnInit,
} from '@angular/core';
import {Geolocation} from '../../../../core/geolocations/types/geolocation';
import {getGeolocationBadges} from '../../helpers/geolocations.helpers';

@Component({
    selector: 'zem-geo-targeting-location',
    templateUrl: './geo-targeting-location.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class GeoTargetingLocationComponent implements OnInit {
    @Input()
    location: Geolocation;
    @Input()
    highlightText: string = '';
    @Input()
    canRemoveLocation: boolean = true;
    @Output()
    removeLocation: EventEmitter<Geolocation> = new EventEmitter<Geolocation>();

    badges: {
        class: string;
        text: string;
    }[] = [];

    ngOnInit() {
        this.badges = getGeolocationBadges(this.location);
    }
}

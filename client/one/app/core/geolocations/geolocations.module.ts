import {NgModule} from '@angular/core';
import {GeolocationsService} from './services/geolocations.service';
import {GeolocationsEndpoint} from './services/geolocations.endpoint';

@NgModule({
    providers: [GeolocationsService, GeolocationsEndpoint],
})
export class GeolocationsModule {}

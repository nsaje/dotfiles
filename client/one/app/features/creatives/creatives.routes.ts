import {Routes} from '@angular/router';
import {CreativesView} from './views/creatives/creatives.view';

export const CREATIVES_ROUTES: Routes = [
    {path: '', pathMatch: 'full', component: CreativesView},
];

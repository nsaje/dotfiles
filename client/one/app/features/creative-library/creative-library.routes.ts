import {Routes} from '@angular/router';
import {CreativeLibraryView} from './views/creative-library/creative-library.view';

export const CREATIVE_LIBRARY_ROUTES: Routes = [
    {path: '', pathMatch: 'full', component: CreativeLibraryView},
];

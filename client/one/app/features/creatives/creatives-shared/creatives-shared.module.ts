import {NgModule} from '@angular/core';

import {SharedModule} from '../../../shared/shared.module';
import {CreativesComponent} from './components/creatives/creatives.component';
import {CreativesActionsComponent} from './components/creatives-actions/creatives-actions.component';
import {CreativesGridComponent} from './components/creatives-grid/creatives-grid.component';
import {CreativeAssetCellComponent} from './components/creative-asset-cell/creative-asset-cell.component';
import {CreativeActionsCellComponent} from './components/creative-actions-cell/creative-actions-cell.component';

const EXPORTED_DECLARATIONS = [
    CreativesComponent,
    CreativesActionsComponent,
    CreativesGridComponent,
    CreativeAssetCellComponent,
    CreativeActionsCellComponent,
];

@NgModule({
    imports: [SharedModule],
    entryComponents: [CreativeAssetCellComponent, CreativeActionsCellComponent],
    declarations: EXPORTED_DECLARATIONS,
    exports: EXPORTED_DECLARATIONS,
})
export class CreativesSharedModule {}

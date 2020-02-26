import {NgModule} from '@angular/core';
import {SharedModule} from '../../shared/shared.module';
import {ArchivedEntityComponent} from './components/archived-entity/archived-entity.component';
import {ArchivedView} from './views/archived/archived.view';
import {CanActivateArchivedEntityGuard} from './route-guards/canActivateArchivedEntity.guard';

@NgModule({
    declarations: [ArchivedEntityComponent, ArchivedView],
    imports: [SharedModule],
    providers: [CanActivateArchivedEntityGuard],
    entryComponents: [ArchivedView],
})
export class ArchivedModule {}

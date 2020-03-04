import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {SidebarContentView} from './views/sidebar-content/sidebar-content.view';
import {SidebarScopeSelectorComponent} from './components/sidebar-scope-selector/sidebar-scope-selector.component';

@NgModule({
    declarations: [SidebarContentView, SidebarScopeSelectorComponent],
    imports: [SharedModule],
    exports: [SidebarContentView],
})
export class SidebarContentModule {}

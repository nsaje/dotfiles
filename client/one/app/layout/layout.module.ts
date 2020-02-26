import {NgModule, Optional, SkipSelf} from '@angular/core';
import {HeaderComponent} from './header/header.component';
import {FilterSelectorComponent} from './filter-selector/filter-selector.component';
import {FooterComponent} from './footer/footer.component';
import {SidebarComponent} from './sidebar/sidebar.component';
import {SidebarContainerComponent} from './sidebar-container/sidebar-container.component';
import {MainContainerComponent} from './main-container/main-container.component';
import {HistoryComponent} from './history/history.component';
import {SharedModule} from '../shared/shared.module';

const EXPORTED_DECLARATIONS = [
    HeaderComponent,
    FilterSelectorComponent,
    FooterComponent,
    SidebarComponent,
    SidebarContainerComponent,
    MainContainerComponent,
    HistoryComponent,
];

@NgModule({
    declarations: [EXPORTED_DECLARATIONS],
    imports: [SharedModule],
    exports: [EXPORTED_DECLARATIONS],
})
export class LayoutModule {
    constructor(
        @Optional()
        @SkipSelf()
        parentModule: LayoutModule
    ) {
        if (parentModule) {
            throw new Error(
                `${LayoutModule.name} has already been loaded. Import ${
                    LayoutModule.name
                } in the AppModule only.`
            );
        }
    }
}

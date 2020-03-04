import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {SidebarScopeSelectorComponent} from './sidebar-scope-selector.component';

describe('DealsLibraryView', () => {
    let component: SidebarScopeSelectorComponent;
    let fixture: ComponentFixture<SidebarScopeSelectorComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [SidebarScopeSelectorComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(SidebarScopeSelectorComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});

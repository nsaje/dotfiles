import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {SidebarContentView} from './sidebar-content.view';
import {SidebarContentStore} from '../../services/sidebar-content.store';
import {AgencyService} from '../../../../core/entities/services/agency/agency.service';
import {AgencyEndpoint} from '../../../../core/entities/services/agency/agency.endpoint';
import {AccountService} from '../../../../core/entities/services/account/account.service';
import {AccountEndpoint} from '../../../../core/entities/services/account/account.endpoint';
import {SidebarScopeSelectorComponent} from '../../components/sidebar-scope-selector/sidebar-scope-selector.component';
import {EntitiesUpdatesService} from '../../../../core/entities/services/entities-updates.service';
import {noop} from 'rxjs';
import {RouterTestingModule} from '@angular/router/testing';
import {AuthStore} from '../../../../core/auth/services/auth.store';

describe('SidebarContentView', () => {
    let component: SidebarContentView;
    let fixture: ComponentFixture<SidebarContentView>;
    let authStoreStub: jasmine.SpyObj<AuthStore>;

    beforeEach(() => {
        authStoreStub = jasmine.createSpyObj(AuthStore.name, [
            'hasAgencyScope',
            'hasPermission',
        ]);

        TestBed.configureTestingModule({
            declarations: [SidebarContentView, SidebarScopeSelectorComponent],
            imports: [
                FormsModule,
                SharedModule,
                RouterTestingModule.withRoutes([]),
            ],
            providers: [
                SidebarContentStore,
                AgencyService,
                AgencyEndpoint,
                AccountService,
                AccountEndpoint,
                EntitiesUpdatesService,
                {
                    provide: AuthStore,
                    useValue: authStoreStub,
                },
            ],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(SidebarContentView);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});

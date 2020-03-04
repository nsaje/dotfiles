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
import {Router, UrlSerializer} from '@angular/router';

describe('SidebarContentView', () => {
    let component: SidebarContentView;
    let fixture: ComponentFixture<SidebarContentView>;
    let zemPermissionsStub: any;
    let mockRouter: any;
    let mockUrlSerializer: any;

    beforeEach(() => {
        zemPermissionsStub = {
            hasAgencyScope: () => noop,
        };
        mockRouter = jasmine.createSpyObj('Router', ['navigate']);
        mockUrlSerializer = jasmine.createSpyObj('UrlSerializer', ['parse']);

        TestBed.configureTestingModule({
            declarations: [SidebarContentView, SidebarScopeSelectorComponent],
            imports: [FormsModule, SharedModule],
            providers: [
                SidebarContentStore,
                AgencyService,
                AgencyEndpoint,
                AccountService,
                AccountEndpoint,
                EntitiesUpdatesService,
                {
                    provide: 'zemPermissions',
                    useValue: zemPermissionsStub,
                },
                {provide: Router, useValue: mockRouter},
                {provide: UrlSerializer, useValue: mockUrlSerializer},
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

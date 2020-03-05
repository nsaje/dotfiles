import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {OperatingSystemListComponent} from './operating-system-list.component';
import {OperatingSystemComponent} from '../operating-system/operating-system.component';
import {TargetOperatingSystem} from '../../../../core/entities/types/common/target-operating-system';

describe('OperatingSystemListComponent', () => {
    let component: OperatingSystemListComponent;
    let fixture: ComponentFixture<OperatingSystemListComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                OperatingSystemListComponent,
                OperatingSystemComponent,
            ],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(OperatingSystemListComponent);
        component = fixture.componentInstance;

        const addOsDropdown = jasmine.createSpyObj('DropdownDirective', [
            'close',
        ]);
        component.addOsDropdown = addOsDropdown;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should allow only selection of desktop OSes if target devices are only desktops', () => {
        component.oses = [];
        component.devices = ['DESKTOP'];
        component.ngOnChanges();

        expect(component.filteredOses.map(os => os.name).sort()).toEqual([
            'CHROMEOS',
            'LINUX',
            'MACOSX',
            'WINDOWS',
        ]);
    });

    it('should allow only selection of tablet OSes if target devices are only tablets', () => {
        component.oses = [];
        component.devices = ['TABLET'];
        component.ngOnChanges();

        expect(component.filteredOses.map(os => os.name).sort()).toEqual([
            'ANDROID',
            'IOS',
            'WINPHONE', // Formally speaking this isn't correct because there are no Windows Phone tablets
            'WINRT',
        ]);
    });

    it('should allow only selection of mobile OSes if target devices are only mobiles', () => {
        component.oses = [];
        component.devices = ['MOBILE'];
        component.ngOnChanges();

        expect(component.filteredOses.map(os => os.name).sort()).toEqual([
            'ANDROID',
            'IOS',
            'WINPHONE',
            'WINRT', // Formally speaking this isn't correct because there are no Windows RT phones
        ]);
    });

    it('should allow selection of all OSes if all devices are targeted', () => {
        component.oses = [];
        component.devices = ['DESKTOP', 'TABLET', 'MOBILE'];
        component.ngOnChanges();

        expect(component.filteredOses.map(os => os.name).sort()).toEqual([
            'ANDROID',
            'CHROMEOS',
            'IOS',
            'LINUX',
            'MACOSX',
            'WINDOWS',
            'WINPHONE',
            'WINRT',
        ]);
    });

    it('should not allow repeated selection of an already selected OS', () => {
        component.oses = [
            {
                name: 'WINDOWS',
                version: {min: 'WINDOWS_XP', max: 'WINDOWS_10'},
            },
        ];
        component.devices = ['DESKTOP'];
        component.ngOnChanges();

        expect(component.filteredOses.map(os => os.name).sort()).toEqual([
            'CHROMEOS',
            'LINUX',
            'MACOSX',
        ]);
    });
});

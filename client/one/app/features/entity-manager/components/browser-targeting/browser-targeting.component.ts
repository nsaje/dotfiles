import './browser-targeting.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnChanges,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {Browser} from '../../../../core/entities/types/common/browser';
import {IncludeExcludeType} from '../../../../app.constants';
import * as arrayHelpers from '../../../../shared/helpers/array.helpers';
import {BrowserTargeting} from '../../types/browser-targeting';
import {
    AVAILABLE_BROWSERS,
    BROWSER_NAMES,
    BROWSER_DEVICE_MAPPING,
} from './browser-targeting.config';
import {INCLUDE_EXCLUDE_TYPES} from '../../entity-manager.config';
import {FormattedBrowser} from '../../types/formatted-browser';
import {BrowserTargetingErrors} from '../../types/browser-targeting-errors';
import {DeviceType} from '../operating-system/types/device-type';

@Component({
    selector: 'zem-browser-targeting',
    templateUrl: './browser-targeting.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BrowserTargetingComponent implements OnChanges {
    @Input()
    includedBrowsers: Browser[];
    @Input()
    excludedBrowsers: Browser[];
    @Input()
    selectedDeviceTypes: DeviceType[];
    @Input()
    isDisabled: boolean;
    @Input()
    browserTargetingErrors: {
        included: BrowserTargetingErrors[];
        excluded: BrowserTargetingErrors[];
    };
    @Output()
    addBrowserTargeting: EventEmitter<BrowserTargeting> = new EventEmitter<
        BrowserTargeting
    >();
    @Output()
    removeBrowserTargeting: EventEmitter<BrowserTargeting> = new EventEmitter<
        BrowserTargeting
    >();
    @Output()
    includeExcludeChange: EventEmitter<IncludeExcludeType> = new EventEmitter<
        IncludeExcludeType
    >();

    availableBrowsers: FormattedBrowser[] = [];
    formattedSelectedBrowsers: FormattedBrowser[] = [];

    includeExcludeType: IncludeExcludeType = IncludeExcludeType.INCLUDE;
    includeExcludeTypes = INCLUDE_EXCLUDE_TYPES;
    includeExcludeEnum = IncludeExcludeType;

    targetingErrors: BrowserTargetingErrors[] = [];
    errorMessage: string;

    ngOnChanges() {
        if (!arrayHelpers.isEmpty(this.excludedBrowsers)) {
            this.formattedSelectedBrowsers = this.getFormattedSelectedBrowsers(
                this.excludedBrowsers
            );
            this.includeExcludeType = IncludeExcludeType.EXCLUDE;
            this.targetingErrors = this.browserTargetingErrors.excluded;
        } else if (!arrayHelpers.isEmpty(this.includedBrowsers)) {
            this.formattedSelectedBrowsers = this.getFormattedSelectedBrowsers(
                this.includedBrowsers
            );
            this.includeExcludeType = IncludeExcludeType.INCLUDE;
            this.targetingErrors = this.browserTargetingErrors.included;
        } else {
            this.formattedSelectedBrowsers = [];
        }
        this.availableBrowsers = this.getAvailableBrowsers(
            AVAILABLE_BROWSERS,
            this.selectedDeviceTypes
        );
        this.errorMessage = this.getErrorMessage(this.targetingErrors);
    }

    onIncludeExcludeChange(includeExcludeType: IncludeExcludeType) {
        this.includeExcludeType = includeExcludeType;
        this.includeExcludeChange.emit(includeExcludeType);
    }

    onAddBrowserTargeting(browser: FormattedBrowser) {
        this.addBrowserTargeting.emit({
            browser: {family: browser.family},
            includeExcludeType: this.includeExcludeType,
        });
    }

    onRemoveBrowserTargeting(browser: FormattedBrowser) {
        this.removeBrowserTargeting.emit({
            browser: {family: browser.family},
            includeExcludeType: this.includeExcludeType,
        });
    }

    private getFormattedSelectedBrowsers(browsers: Browser[]) {
        return browsers.map(browser => {
            return {
                family: browser.family,
                name: BROWSER_NAMES[browser.family],
            };
        });
    }

    private getAvailableBrowsers(
        browsers: FormattedBrowser[],
        selectedDeviceTypes: DeviceType[]
    ) {
        return browsers.filter(browser => {
            return arrayHelpers.includesAny(
                BROWSER_DEVICE_MAPPING[browser.family],
                selectedDeviceTypes
            );
        });
    }

    private getErrorMessage(targetingErrors: BrowserTargetingErrors[]) {
        const error = targetingErrors.find(targetingError => {
            return targetingError?.family?.length;
        });
        return error ? error.family[0] : null;
    }
}

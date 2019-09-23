import './deals-library.view.less';

import {Component, ChangeDetectionStrategy} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';

@Component({
    selector: 'zem-deals-library-view',
    templateUrl: './deals-library.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DealsLibraryView {}

declare var angular: angular.IAngularStatic;
angular
    .module('one.downgraded')
    .directive(
        'zemDealsLibraryView',
        downgradeComponent({component: DealsLibraryView})
    );

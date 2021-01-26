import './loader.component.less';

import {Component, Input} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';

@Component({
    selector: 'zem-loader',
    templateUrl: './loader.component.html',
})
export class LoaderComponent {
    @Input()
    description: string;
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemLoader',
    downgradeComponent({
        component: LoaderComponent,
        propagateDigest: false,
    })
);

import 'ngx-toastr/toastr.css';

import {Injectable} from '@angular/core';
import {ToastrService} from 'ngx-toastr';
import {IndividualConfig} from 'ngx-toastr/toastr/toastr-config';
import {NotificationOptions} from '../types/notification-options';
import {downgradeInjectable} from '@angular/upgrade/static';

@Injectable()
export class NotificationService {
    constructor(private toastr: ToastrService) {}

    info(message: string, title?: string, options?: NotificationOptions) {
        this.toastr.info(message, title, this.getToastrOptions(options));
    }

    success(message: string, title?: string, options?: NotificationOptions) {
        this.toastr.success(message, title, this.getToastrOptions(options));
    }

    warning(message: string, title?: string, options?: NotificationOptions) {
        this.toastr.warning(message, title, this.getToastrOptions(options));
    }

    error(message: string, title?: string, options?: NotificationOptions) {
        this.toastr.error(message, title, this.getToastrOptions(options));
    }

    private getToastrOptions(
        options?: NotificationOptions
    ): Partial<IndividualConfig> {
        options = options || {};
        return {
            timeOut: options.timeout || 0,
        };
    }
}

declare var angular: angular.IAngularStatic;
angular
    .module('one.downgraded')
    .factory(
        'zemNotificationService',
        downgradeInjectable(NotificationService)
    );

import {Injectable} from '@angular/core';
import {downgradeInjectable} from '@angular/upgrade/static';
import {ActionMessage} from '../../../workers/shared/types/action-message';
import {ActionTopic} from '../../../workers/shared/workers.constants';
import {APP_CONFIG} from '../../app.config';
import * as commonHelpers from '../../shared/helpers/common.helpers';

@Injectable()
export class WorkersService {
    async runWorker<T1, T2>(topic: ActionTopic, payload: T1): Promise<T2> {
        return new Promise<T2>((resolve, reject) => {
            if (commonHelpers.isDefined(typeof Worker)) {
                const worker = this.createWorker(APP_CONFIG.workerUrl);
                worker.onmessage = ($event: MessageEvent) => {
                    worker.terminate();
                    resolve($event.data);
                };
                worker.onerror = ($event: ErrorEvent) => {
                    worker.terminate();
                    reject($event.error);
                };
                worker.postMessage({
                    topic: topic,
                    payload: payload,
                } as ActionMessage);
            } else {
                reject('Worker not supported');
            }
        });
    }

    private createWorker(workerPath: string): Worker {
        const blob = new Blob(["importScripts('" + workerPath + "');"], {
            type: 'application/javascript',
        });
        const url = window.URL || window.webkitURL;
        const blobUrl = url.createObjectURL(blob);
        return new Worker(blobUrl);
    }
}

declare var angular: angular.IAngularStatic;
angular
    .module('one.downgraded')
    .factory('zemWorkersService', downgradeInjectable(WorkersService));

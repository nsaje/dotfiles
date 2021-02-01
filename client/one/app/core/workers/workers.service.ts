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
                this.postMessage(worker, topic, payload);
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

    private postMessage<T1>(
        worker: Worker,
        topic: ActionTopic,
        payload: T1
    ): void {
        if (Array.isArray(payload)) {
            // Communicating Large Objects with Web Workers in javascript
            // https://developers.redhat.com/blog/2014/05/20/communicating-large-objects-with-web-workers-in-javascript/
            const payloadLength = payload.length;
            let index = 0;
            (function doChunk() {
                let chunkSize = 100;
                while (chunkSize > 0 && index < payload.length) {
                    worker.postMessage(
                        JSON.stringify({
                            topic: topic,
                            payload: payload[index],
                            payloadLength: payloadLength,
                        } as ActionMessage)
                    );
                    --chunkSize;
                    ++index;
                }
                if (index < payload.length) {
                    setTimeout(doChunk, 0);
                }
            })();
        } else {
            worker.postMessage(
                JSON.stringify({
                    topic: topic,
                    payload: payload,
                } as ActionMessage)
            );
        }
    }
}

declare var angular: angular.IAngularStatic;
angular
    .module('one.downgraded')
    .factory('zemWorkersService', downgradeInjectable(WorkersService));

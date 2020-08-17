import {NgModule} from '@angular/core';
import {FetchCurrentUserActionEffect} from './services/effects/fetch-current-user.effect';
import {AuthStore} from './services/auth.store';

@NgModule({
    providers: [FetchCurrentUserActionEffect, AuthStore],
})
export class AuthModule {}

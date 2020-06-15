import {NgModule} from '@angular/core';
import {UsersEndpoint} from './services/users.endpoint';
import {UsersService} from './services/users.service';

@NgModule({
    providers: [UsersEndpoint, UsersService],
})
export class UsersModule {}
